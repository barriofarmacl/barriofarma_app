# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
DocType Prescription para gestionar recetas médicas según el modelo DDD
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class Prescription(Document):
	"""
	Extensión de la clase Prescription para implementar validaciones
	específicas del dominio farmacéutico según el modelo DDD
	"""

	def validate(self):
		"""
		Valida las invariantes del agregado Prescription según el modelo DDD
		"""
		# Validar invariantes del dominio farmacéutico
		self.validate_doctor_license()
		self.validate_patient_required()
		self.validate_items_required()
		self.validate_temporal_validity()
		self.validate_dispensation_limits()
		self.validate_item_quantities()
		self.validate_expired_prescription()
		self.update_status()

	def validate_doctor_license(self):
		"""
		Invariante: Una receta debe estar asociada a un médico con licencia válida
		"""
		if not self.get("doctor_license") or not self.get("doctor_license").strip():
			frappe.throw(
				_("El número de licencia médica (doctor_license) es obligatorio"),
				title=_("Licencia Médica Requerida")
			)

	def validate_patient_required(self):
		"""
		Invariante: Una receta debe estar asociada a un paciente específico
		"""
		if not self.get("patient"):
			frappe.throw(
				_("El paciente (patient) es obligatorio"),
				title=_("Paciente Requerido")
			)
		
		# Verificar que el Patient existe
		if not frappe.db.exists("Patient", self.patient):
			frappe.throw(
				_("El paciente '{0}' no existe").format(self.patient),
				title=_("Paciente Inválido")
			)

		if not self.get("patient_name") or not self.get("patient_name").strip():
			frappe.throw(
				_("El nombre del paciente (patient_name) es obligatorio"),
				title=_("Nombre de Paciente Requerido")
			)

	def validate_items_required(self):
		"""
		Invariante: Una receta debe tener al menos un medicamento prescrito
		"""
		if not self.get("items") or len(self.items) == 0:
			frappe.throw(
				_("Una receta debe tener al menos un medicamento prescrito"),
				title=_("Items Requeridos")
			)

	def validate_temporal_validity(self):
		"""
		Invariante: Una receta solo puede dispensarse dentro de su periodo de validez
		valid_till debe ser posterior o igual a prescription_date
		"""
		if self.get("prescription_date") and self.get("valid_till"):
			prescription_date = getdate(self.prescription_date)
			valid_till = getdate(self.valid_till)

			if valid_till < prescription_date:
				frappe.throw(
					_("La fecha de validez (valid_till) debe ser posterior o igual a la fecha de emisión (prescription_date)"),
					title=_("Validez Temporal Inválida")
				)

	def validate_dispensation_limits(self):
		"""
		Invariante: No se puede exceder el número máximo de dispensaciones especificado
		"""
		max_dispensations = self.get("max_dispensations") or 0
		dispensation_count = self.get("dispensation_count") or 0

		if dispensation_count > max_dispensations:
			frappe.throw(
				_("El número de dispensaciones realizadas ({0}) no puede exceder el máximo permitido ({1})").format(
					dispensation_count, max_dispensations
				),
				title=_("Límite de Dispensaciones Excedido")
			)

	def validate_item_quantities(self):
		"""
		Invariante: La cantidad dispensada no puede exceder la cantidad prescrita por ítem
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
						title=_("Cantidad Dispensada Inválida")
					)

	def validate_expired_prescription(self):
		"""
		Regla de Negocio: Una receta vencida no puede ser utilizada para dispensación
		Si el estado es "Vencida", no se puede modificar las cantidades dispensadas
		"""
		from frappe.utils import today, getdate

		if self.get("status") == "Vencida":
			# Si está vencida, no se puede dispensar más
			if self.get("items"):
				for item in self.items:
					current_dispensed_qty = item.get("dispensed_qty") or 0
					# Si hay cambios en dispensed_qty y la receta está vencida, lanzar error
					if hasattr(self, "_original") and self._original:
						original_item = next(
							(orig_item for orig_item in self._original.get("items", []) if orig_item.name == item.name),
							None
						)
						if original_item and current_dispensed_qty > (original_item.get("dispensed_qty") or 0):
							frappe.throw(
								_("No se puede dispensar en una receta vencida"),
								title=_("Receta Vencida")
							)

		# Verificar si la receta está vencida según la fecha
		if self.get("valid_till"):
			valid_till = getdate(self.valid_till)
			current_date = getdate(today())

			if valid_till < current_date and self.get("status") != "Vencida":
				# Actualizar estado a vencida si la fecha de validez ha pasado
				self.status = "Vencida"

			# Si la receta está vencida y se intenta dispensar, lanzar error
			if valid_till < current_date:
				if self.get("items"):
					for item in self.items:
						current_dispensed_qty = item.get("dispensed_qty") or 0
						# Si hay cambios en dispensed_qty y la receta está vencida, lanzar error
						if hasattr(self, "_original") and self._original:
							original_item = next(
								(orig_item for orig_item in self._original.get("items", []) if orig_item.name == item.name),
								None
							)
							if original_item and current_dispensed_qty > (original_item.get("dispensed_qty") or 0):
								frappe.throw(
									_("No se puede dispensar en una receta vencida (válida hasta {0})").format(
										valid_till.strftime("%d/%m/%Y")
									),
									title=_("Receta Vencida")
								)
						# Si la receta está vencida y tiene dispensed_qty > 0, no permitir dispensación
						# (incluso si no hay _original disponible)
						elif current_dispensed_qty > 0 and not self.is_new():
							# Verificar si el item tenía dispensed_qty = 0 al cargar desde BD
							if hasattr(item, '_doc_before_save'):
								original_qty = item._doc_before_save.get("dispensed_qty") or 0
								if current_dispensed_qty > original_qty:
									frappe.throw(
										_("No se puede dispensar en una receta vencida (válida hasta {0})").format(
											valid_till.strftime("%d/%m/%Y")
										),
										title=_("Receta Vencida")
									)
							else:
								# Si no hay _doc_before_save, asumir que cualquier dispensed_qty > 0 es un cambio
								# solo si el estado es "Vencida" y se está intentando dispensar
								if self.get("status") == "Vencida" and current_dispensed_qty > 0:
									frappe.throw(
										_("No se puede dispensar en una receta vencida (válida hasta {0})").format(
											valid_till.strftime("%d/%m/%Y")
										),
										title=_("Receta Vencida")
									)

	def update_status(self):
		"""
		Actualiza el estado de la receta automáticamente según las dispensaciones
		"""
		if not self.get("items"):
			return

		total_items = len(self.items)
		total_dispensed = sum(1 for item in self.items if (item.get("dispensed_qty") or 0) > 0)
		total_completed = sum(
			1 for item in self.items
			if (item.get("dispensed_qty") or 0) >= (item.get("quantity") or 0) and (item.get("quantity") or 0) > 0
		)

		# Si todos los items están completamente dispensados
		if total_completed == total_items and total_items > 0:
			self.status = "Completada"
		# Si al menos un item está parcialmente dispensado
		elif total_dispensed > 0 and total_completed < total_items:
			self.status = "Parcialmente Dispensada"
		# Si ningún item ha sido dispensado y la receta no está vencida
		elif total_dispensed == 0 and self.get("status") != "Vencida":
			self.status = "Nueva"

