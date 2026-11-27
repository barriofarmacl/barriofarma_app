# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Costo de bodega en la línea de la boleta de caja.

ERPNext no ejecuta set_incoming_rate en una venta POS normal, así que
incoming_rate queda en 0 y check_zero_rate avisa aunque el libro tenga costo.
El cierre sí recalcula ese costo al armar la Sales Invoice. Aquí se copia el
mismo lookup a la línea para que el aviso quede solo cuando el costo es cero.
"""

import frappe
from frappe.utils import cint, flt, nowtime


def copy_pos_warehouse_incoming_rate(doc, rate_for_row=None, is_stock_item=None):
	"""Escribe el costo de la bodega en incoming_rate de una venta POS.

	No toca devoluciones: ese camino lo resuelve ERPNext. Un lookup en cero
	se deja en cero para que el aviso de costo faltante siga visible.
	"""
	if doc.get("is_return"):
		return
	if not cint(doc.get("update_stock")):
		return

	lookup = rate_for_row or warehouse_incoming_rate
	stock_item = is_stock_item or item_is_stock_item

	for row in doc.get("items") or []:
		item_code = row.get("item_code")
		if not item_code or not stock_item(item_code):
			continue
		warehouse = row.get("warehouse") or doc.get("set_warehouse")
		if not warehouse:
			continue
		rate = flt(lookup(doc, row, warehouse))
		if rate:
			row.incoming_rate = rate


def item_is_stock_item(item_code):
	return bool(frappe.get_cached_value("Item", item_code, "is_stock_item"))


def warehouse_incoming_rate(doc, row, warehouse):
	"""Mismo criterio que el cierre: _get_incoming_rate, sin cortar la venta si falta costo."""
	from erpnext.stock.utils import _get_incoming_rate

	qty = flt(row.get("stock_qty") or row.get("qty"))
	return _get_incoming_rate(
		{
			"item_code": row.get("item_code"),
			"warehouse": warehouse,
			"posting_date": doc.get("posting_date"),
			"posting_time": doc.get("posting_time") or nowtime(),
			"qty": -1 * qty,
			"serial_and_batch_bundle": row.get("serial_and_batch_bundle"),
			"company": doc.get("company"),
			"voucher_type": doc.get("doctype") or "POS Invoice",
			"voucher_no": doc.get("name"),
			"voucher_detail_no": row.get("name"),
			"allow_zero_valuation": row.get("allow_zero_valuation_rate"),
			"batch_no": row.get("batch_no"),
			"serial_no": row.get("serial_no"),
		},
		raise_error_if_no_rate=False,
		fallbacks=True,
	)
