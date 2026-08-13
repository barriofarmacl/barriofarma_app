# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Dispensacion de Receta Medica desde ventas POS / Sales Invoice."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, formatdate, getdate

RECETA_MEDICA_DT = "Receta Medica"
INVOICE_DOCTYPES = ("POS Invoice", "Sales Invoice")


def aggregate_dispensed_qty_from_invoices(receta_name: str) -> dict[str, float]:
	"""Total entregado por item_code desde ventas submitidas vinculadas a la receta."""
	qty_by_item: dict[str, float] = {}
	for doctype in INVOICE_DOCTYPES:
		for inv_name in frappe.get_all(
			doctype,
			filters={"custom_receta_medica": receta_name, "docstatus": 1},
			pluck="name",
		):
			invoice = frappe.get_doc(doctype, inv_name)
			for row in invoice.get("items") or []:
				code = row.get("item_code")
				if code:
					qty_by_item[code] = qty_by_item.get(code, 0) + flt(row.get("qty"))
	return qty_by_item


def count_submitted_invoices_for_receta(receta_name: str) -> int:
	return sum(
		len(
			frappe.get_all(
				doctype,
				filters={"custom_receta_medica": receta_name, "docstatus": 1},
				pluck="name",
			)
		)
		for doctype in INVOICE_DOCTYPES
	)


def reconcile_receta_dispensed_qty(receta, persist: bool = False) -> bool:
	"""
	Alinea dispensed_qty y dispensation_count con ventas submitidas vinculadas.
	"""
	aggregated = aggregate_dispensed_qty_from_invoices(receta.name)
	expected_count = count_submitted_invoices_for_receta(receta.name)
	changed = False

	if int(receta.get("dispensation_count") or 0) != expected_count:
		receta.dispensation_count = expected_count
		changed = True

	for row in receta.get("items") or []:
		item_code = row.get("item")
		if not item_code:
			continue
		prescribed = flt(row.get("quantity"))
		expected = aggregated.get(item_code, 0)
		if prescribed:
			expected = min(prescribed, expected)
		if flt(row.get("dispensed_qty")) != expected:
			row.dispensed_qty = expected
			changed = True

	old_status = receta.get("status")
	receta.update_status()
	if receta.get("status") != old_status:
		changed = True

	if persist and changed:
		receta.save(ignore_permissions=True)
		frappe.db.commit()

	return changed


def apply_invoice_qty_to_receta_items(receta, invoice_doc) -> None:
	"""Suma cantidades vendidas a dispensed_qty por linea de medicamento."""
	qty_by_item: dict[str, float] = {}
	for row in invoice_doc.get("items") or []:
		code = row.get("item_code")
		if code:
			qty_by_item[code] = qty_by_item.get(code, 0) + flt(row.get("qty"))

	for receta_row in receta.get("items") or []:
		item_code = receta_row.get("item")
		if not item_code or item_code not in qty_by_item:
			continue
		prescribed = flt(receta_row.get("quantity"))
		current = flt(receta_row.get("dispensed_qty"))
		added = qty_by_item[item_code]
		receta_row.dispensed_qty = min(prescribed, current + added) if prescribed else current + added


def get_receta_medica_pos_summary(receta_name: str) -> dict:
	"""Resumen para panel POS al seleccionar una receta."""
	if not frappe.db.exists(RECETA_MEDICA_DT, receta_name):
		frappe.throw(
			_("La receta '{0}' no existe.").format(receta_name),
			title=_("Receta No Encontrada"),
		)

	receta = frappe.get_doc(RECETA_MEDICA_DT, receta_name)
	reconcile_receta_dispensed_qty(receta, persist=True)

	max_disp = int(receta.get("max_dispensations") or 0)
	disp_count = int(receta.get("dispensation_count") or 0)
	valid_till = receta.get("valid_till")

	items = []
	for row in receta.get("items") or []:
		prescribed = flt(row.get("quantity"))
		dispensed = flt(row.get("dispensed_qty"))
		items.append(
			{
				"item": row.get("item"),
				"item_name": row.get("item_name"),
				"quantity": prescribed,
				"dispensed_qty": dispensed,
				"pending_qty": max(prescribed - dispensed, 0),
			}
		)

	return {
		"name": receta.name,
		"status": receta.get("status"),
		"valid_till": valid_till,
		"valid_till_display": formatdate(getdate(valid_till)) if valid_till else "",
		"max_dispensations": max_disp,
		"dispensation_count": disp_count,
		"pending_dispensations": max(max_disp - disp_count, 0),
		"items": items,
	}
