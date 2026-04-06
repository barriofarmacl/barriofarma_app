# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Validacion de vigencia de Receta Medica para ventas (Story 5.2).
"""

import frappe
from frappe import _
from frappe.utils import getdate, today

from barriofarma_app.barriofarma_app.utils.domain.receta_medica_items import validate_all_receta_medica_items_included

RECETA_MEDICA_DT = "Receta Medica"
RECETA_MEDICA_DISPENSACION_DT = "Receta Medica Dispensacion"


def validate_receta_medica_validity(doc, method=None):
	"""
	Validar que la receta asociada (custom_receta_medica) este vigente y no exceda limites.
	"""
	receta_name = doc.get("custom_receta_medica")

	if not receta_name:
		items_requiring_prescription = []
		for item in doc.get("items", []):
			if item.item_code:
				try:
					item_doc = frappe.get_doc("Item", item.item_code)
					if item_doc.get("custom_requires_prescription_retention"):
						items_requiring_prescription.append(item.item_code)
				except frappe.DoesNotExistError:
					continue

		if items_requiring_prescription:
			items_list = ", ".join([frappe.bold(item) for item in items_requiring_prescription])
			frappe.throw(
				_("Esta venta incluye productos que requieren receta medica: {0}. Asocie una receta valida en el campo 'Receta Medica'.").format(
					items_list
				),
				title=_("Receta Requerida")
			)
		return

	if not frappe.db.exists(RECETA_MEDICA_DT, receta_name):
		frappe.throw(
			_("La receta '{0}' no existe.").format(receta_name),
			title=_("Receta No Encontrada")
		)

	try:
		receta = frappe.get_doc(RECETA_MEDICA_DT, receta_name)
	except (frappe.DoesNotExistError, Exception):
		frappe.throw(
			_("La receta '{0}' no existe.").format(receta_name),
			title=_("Receta No Encontrada")
		)

	if receta.get("valid_till"):
		valid_till = getdate(receta.valid_till)
		current_date = getdate(today())
		if valid_till < current_date:
			frappe.throw(
				_("La receta '{0}' esta vencida (valida hasta {1}). No se puede usar para dispensar.").format(
					receta_name, valid_till.strftime("%d/%m/%Y")
				),
				title=_("Receta Vencida")
			)

	max_dispensations = receta.get("max_dispensations") or 0
	dispensation_count = receta.get("dispensation_count") or 0
	if dispensation_count >= max_dispensations:
		frappe.throw(
			_("La receta '{0}' ha alcanzado el limite maximo de dispensaciones ({1}/{2}).").format(
				receta_name, dispensation_count, max_dispensations
			),
			title=_("Limite de Dispensaciones Alcanzado")
		)

	if receta.get("status") == "Vencida":
		frappe.throw(
			_("La receta '{0}' esta en estado 'Vencida' y no puede usarse para dispensar.").format(receta_name),
			title=_("Estado de Receta Invalido")
		)

	validate_all_receta_medica_items_included(doc, method)


def update_receta_medica_dispensation(doc, method=None):
	"""
	Al confirmar venta: incrementar dispensation_count, actualizar estado y anadir fila a Receta Medica Dispensacion.
	Un solo save() para evitar doble escritura.
	"""
	receta_name = doc.get("custom_receta_medica")

	if not receta_name:
		return

	if not frappe.db.exists(RECETA_MEDICA_DT, receta_name):
		frappe.log_error(
			message=f"Receta Medica {receta_name} no encontrada al actualizar dispensacion desde {doc.doctype} {doc.name}",
			title="Error al Actualizar Dispensacion"
		)
		return

	try:
		receta = frappe.get_doc(RECETA_MEDICA_DT, receta_name)
		receta.dispensation_count = (receta.get("dispensation_count") or 0) + 1
		receta.update_status()

		receta.append("related_sales_invoices", {
			"doctype": RECETA_MEDICA_DISPENSACION_DT,
			"sales_invoice": doc.name,
			"date": doc.posting_date or today(),
			"dispensed_by": frappe.session.user,
			"notes": f"Dispensacion desde {doc.doctype} {doc.name}"
		})

		receta.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(
			message=f"Error al actualizar dispensacion de receta {receta_name} desde {doc.doctype} {doc.name}: {frappe.get_traceback()}",
			title="Error al Actualizar Dispensacion"
		)
		frappe.db.rollback()
