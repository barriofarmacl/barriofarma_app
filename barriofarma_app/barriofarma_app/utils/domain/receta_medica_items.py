# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Utilidades para items de Receta Medica en ventas (Story 5.3).
"""

import frappe
from frappe import _
from frappe.utils import flt

RECETA_MEDICA_DT = "Receta Medica"


def get_receta_medica_items(receta_name):
	"""
	Obtener todos los items de una Receta Medica.

	Args:
		receta_name: Nombre del documento Receta Medica

	Returns:
		Lista de diccionarios con item_code, item_name, quantity, uom, rate, prescription_item_name
	"""
	if not frappe.db.exists(RECETA_MEDICA_DT, receta_name):
		frappe.throw(
			_("La receta '{0}' no existe.").format(receta_name),
			title=_("Receta No Encontrada")
		)

	try:
		receta = frappe.get_doc(RECETA_MEDICA_DT, receta_name)
	except frappe.DoesNotExistError:
		frappe.throw(
			_("La receta '{0}' no existe.").format(receta_name),
			title=_("Receta No Encontrada")
		)

	items = []
	for row in receta.get("items", []):
		item_code = row.get("item")
		quantity = flt(row.get("quantity", 0))

		if not item_code or quantity <= 0:
			continue

		try:
			item_doc = frappe.get_doc("Item", item_code)
		except frappe.DoesNotExistError:
			frappe.log_error(
				message=f"Item {item_code} de receta {receta_name} no existe",
				title="Error al Obtener Items de Receta Medica"
			)
			continue

		items.append({
			"item_code": item_code,
			"item_name": item_doc.item_name,
			"quantity": quantity,
			"uom": item_doc.stock_uom or "Unit",
			"rate": item_doc.standard_rate or 0,
			"prescription_item_name": row.name
		})

	return items


def add_receta_medica_items_to_invoice(invoice_name, receta_name, warehouse=None):
	"""
	Agregar todos los items de una Receta Medica a una venta (Sales Invoice o POS Invoice).
	"""
	invoice_doctype = None
	if frappe.db.exists("Sales Invoice", invoice_name):
		invoice_doctype = "Sales Invoice"
	elif frappe.db.exists("POS Invoice", invoice_name):
		invoice_doctype = "POS Invoice"
	else:
		frappe.throw(
			_("La venta '{0}' no existe.").format(invoice_name),
			title=_("Venta No Encontrada")
		)

	prescription_items = get_receta_medica_items(receta_name)

	if not prescription_items:
		frappe.throw(
			_("La receta '{0}' no tiene medicamentos prescritos.").format(receta_name),
			title=_("Receta Sin Items")
		)

	invoice = frappe.get_doc(invoice_doctype, invoice_name)
	items_added = []
	items_skipped = []

	for prescription_item in prescription_items:
		item_code = prescription_item["item_code"]
		quantity = prescription_item["quantity"]

		item_exists = False
		for existing_item in invoice.get("items", []):
			if existing_item.item_code == item_code:
				item_exists = True
				items_skipped.append({"item_code": item_code, "reason": "Item ya existe en la venta"})
				break

		if not item_exists:
			item_dict = {
				"item_code": item_code,
				"item_name": prescription_item["item_name"],
				"qty": quantity,
				"uom": prescription_item["uom"],
				"rate": prescription_item["rate"],
				"warehouse": warehouse or invoice.get("set_warehouse")
			}
			invoice.append("items", item_dict)
			items_added.append({"item_code": item_code, "quantity": quantity})

	invoice.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"items_added": items_added,
		"items_skipped": items_skipped,
		"total_items": len(prescription_items)
	}


def validate_all_receta_medica_items_included(doc, method=None):
	"""
	Validar que todos los medicamentos de la Receta Medica asociada estan en la venta.
	"""
	receta_name = doc.get("custom_receta_medica")

	if not receta_name:
		return

	if not frappe.db.exists(RECETA_MEDICA_DT, receta_name):
		return

	try:
		receta = frappe.get_doc(RECETA_MEDICA_DT, receta_name)
	except frappe.DoesNotExistError:
		return

	prescription_item_codes = set()
	for row in receta.get("items", []):
		item_code = row.get("item")
		if item_code:
			prescription_item_codes.add(item_code)

	if not prescription_item_codes:
		return

	invoice_item_codes = set()
	for invoice_item in doc.get("items", []):
		item_code = invoice_item.get("item_code")
		if item_code:
			invoice_item_codes.add(item_code)

	missing_items = prescription_item_codes - invoice_item_codes

	if missing_items:
		missing_list = ", ".join([frappe.bold(item) for item in sorted(missing_items)])
		frappe.throw(
			_("La receta '{0}' incluye medicamentos que no estan en esta venta: {1}. Agregue todos los medicamentos de la receta o quite la asociacion.").format(
				receta_name, missing_list
			),
			title=_("Items de Receta Faltantes")
		)
