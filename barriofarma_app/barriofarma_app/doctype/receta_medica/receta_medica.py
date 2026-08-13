# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
DocType Receta Medica para gestionar recetas medicas segun el modelo DDD (lenguaje ubicuo BarrioFarma).
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class RecetaMedica(Document):
	"""
	Agregado Receta Medica: validaciones e invariantes del dominio farmaceutico.
	"""

	def validate(self):
		"""
		Valida las invariantes del agregado Receta Medica segun el modelo DDD.
		"""
		self.validate_patient_required()
		self.validate_items_required()
		self.validate_temporal_validity()
		self.validate_dispensation_limits()
		self.validate_item_quantities()
		self.validate_expired_receta()
		self.update_status()

	def validate_patient_required(self):
		"""
		Invariante: Una receta debe estar asociada a un paciente especifico.
		"""
		if not self.get("patient"):
			frappe.throw(
				_("El paciente (patient) es obligatorio"),
				title=_("Paciente Requerido")
			)

		if not frappe.db.exists("Patient", self.patient):
			frappe.throw(
				_("El paciente '{0}' no existe").format(self.patient),
				title=_("Paciente Invalido")
			)

		if not self.get("patient_name") or not self.get("patient_name").strip():
			frappe.throw(
				_("El nombre del paciente (patient_name) es obligatorio"),
				title=_("Nombre de Paciente Requerido")
			)

	def validate_items_required(self):
		"""
		Invariante: Una receta debe tener al menos un medicamento prescrito.
		"""
		if not self.get("items") or len(self.items) == 0:
			frappe.throw(
				_("Una receta debe tener al menos un medicamento prescrito"),
				title=_("Items Requeridos")
			)

	def validate_temporal_validity(self):
		"""
		Invariante: valid_till debe ser posterior o igual a prescription_date.
		"""
		if not self.get("prescription_date"):
			frappe.throw(
				_("La fecha de emision (prescription_date) es obligatoria"),
				title=_("Fecha de Emision Requerida")
			)

		if not self.get("valid_till"):
			frappe.throw(
				_("La fecha de validez (valid_till) es obligatoria"),
				title=_("Fecha de Validez Requerida")
			)

		if self.get("prescription_date") and self.get("valid_till"):
			prescription_date = getdate(self.prescription_date)
			valid_till = getdate(self.valid_till)

			if valid_till < prescription_date:
				frappe.throw(
					_("La fecha de validez (valid_till) debe ser posterior o igual a la fecha de emision (prescription_date)"),
					title=_("Validez Temporal Invalida")
				)

	def validate_dispensation_limits(self):
		"""
		Invariante: No se puede exceder el numero maximo de dispensaciones; max_dispensations >= 1.
		"""
		max_dispensations = self.get("max_dispensations") or 0
		dispensation_count = self.get("dispensation_count") or 0

		if max_dispensations < 1:
			frappe.throw(
				_("El numero maximo de dispensaciones debe ser al menos 1"),
				title=_("Limite de Dispensaciones Invalido")
			)

		if dispensation_count > max_dispensations:
			frappe.throw(
				_("El numero de dispensaciones realizadas ({0}) no puede exceder el maximo permitido ({1})").format(
					dispensation_count, max_dispensations
				),
				title=_("Limite de Dispensaciones Excedido")
			)

	def validate_item_quantities(self):
		"""
		Invariante: La cantidad dispensada no puede exceder la cantidad prescrita por item.
		"""
		if self.get("items"):
			for item in self.items:
				quantity = item.get("quantity") or 0
				dispensed_qty = item.get("dispensed_qty") or 0

				if dispensed_qty > quantity:
					frappe.throw(
						_("La cantidad dispensada ({0}) del medicamento '{1}' no puede exceder la cantidad prescrita ({2})").format(
							dispensed_qty, item.get("item_name") or item.get("item"), quantity
						),
						title=_("Cantidad Dispensada Invalida")
					)

	def validate_expired_receta(self):
		"""
		Regla de Negocio: Una receta vencida no puede ser utilizada para dispensacion.
		Usa get_doc_before_save() cuando este disponible para detectar cambios en dispensed_qty.
		"""
		from frappe.utils import today, getdate

		if self.get("status") == "Vencida":
			if self.get("items"):
				for item in self.items:
					current_dispensed_qty = item.get("dispensed_qty") or 0
					doc_before = self.get_doc_before_save()
					if doc_before and doc_before.get("items"):
						original_item = next(
							(orig for orig in doc_before.get("items", []) if orig.name == item.name),
							None
						)
						if original_item and current_dispensed_qty > (original_item.get("dispensed_qty") or 0):
							frappe.throw(
								_("No se puede dispensar en una receta vencida"),
								title=_("Receta Vencida")
							)

		if self.get("valid_till"):
			valid_till = getdate(self.valid_till)
			current_date = getdate(today())

			if valid_till < current_date and self.get("status") != "Vencida":
				self.status = "Vencida"

			if valid_till < current_date and self.get("items"):
				for item in self.items:
					current_dispensed_qty = item.get("dispensed_qty") or 0
					doc_before = self.get_doc_before_save()
					if doc_before and doc_before.get("items"):
						original_item = next(
							(orig for orig in doc_before.get("items", []) if orig.name == item.name),
							None
						)
						if original_item and current_dispensed_qty > (original_item.get("dispensed_qty") or 0):
							frappe.throw(
								_("No se puede dispensar en una receta vencida (valida hasta {0})").format(
									valid_till.strftime("%d/%m/%Y")
								),
								title=_("Receta Vencida")
							)
					elif not self.is_new() and self.get("status") == "Vencida" and current_dispensed_qty > 0:
						frappe.throw(
							_("No se puede dispensar en una receta vencida (valida hasta {0})").format(
								valid_till.strftime("%d/%m/%Y")
							),
							title=_("Receta Vencida")
						)

	def update_status(self):
		"""
		Actualiza el estado segun visitas (dispensation_count) y cantidades por item.
		"""
		if self.get("status") == "Vencida":
			return

		max_dispensations = int(self.get("max_dispensations") or 1)
		dispensation_count = int(self.get("dispensation_count") or 0)
		items = self.get("items") or []

		items_with_qty = [row for row in items if flt(row.get("quantity")) > 0]
		all_item_qty_complete = bool(items_with_qty) and all(
			flt(row.get("dispensed_qty")) >= flt(row.get("quantity")) for row in items_with_qty
		)
		any_item_dispensed = any(flt(row.get("dispensed_qty")) > 0 for row in items)
		visits_complete = dispensation_count >= max_dispensations

		if visits_complete or all_item_qty_complete:
			self.status = "Completada"
		elif dispensation_count > 0 or any_item_dispensed:
			self.status = "Parcialmente Dispensada"
		else:
			self.status = "Nueva"
