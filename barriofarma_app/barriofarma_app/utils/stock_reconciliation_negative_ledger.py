# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Aviso cuando una conciliación parte de un libro de inventario negativo.

ERPNext valida el movimiento con saldo_anterior + actual_qty antes de aplicar
el conteo absoluto de la conciliación. Si el saldo anterior es negativo y
actual_qty llega en 0, el envío se rechaza con un mensaje de unidades
faltantes que no explica la causa.
"""

import frappe
from frappe import _
from frappe.utils import escape_html, flt, formatdate, format_time


def enforce_negative_ledger_on_submit(doc):
	if getattr(doc, "_action", None) != "submit":
		return
	if doc.get("purpose") not in (None, "", "Stock Reconciliation"):
		return
	blocks = collect_negative_ledger_blocks(doc.posting_date, doc.posting_time, doc.get("items") or [])
	if not blocks:
		return
	frappe.throw(
		detail_lines(blocks),
		title=_("Libro de inventario en negativo"),
		as_list=True,
	)


@frappe.whitelist()
def negative_ledger_warning(posting_date, posting_time=None, items=None, purpose=None):
	"""Texto para el aviso rojo del formulario. Vacío si el libro no está en negativo."""
	frappe.has_permission("Stock Reconciliation", "read", throw=True)
	if isinstance(items, str):
		items = frappe.parse_json(items)
	if purpose not in (None, "", "Stock Reconciliation"):
		return ""
	blocks = collect_negative_ledger_blocks(posting_date, posting_time, items or [])
	if not blocks:
		return ""
	return headline(blocks)


def collect_negative_ledger_blocks(posting_date, posting_time, rows):
	if not posting_date:
		return []
	from erpnext.stock.stock_ledger import get_previous_sle

	blocks = []
	for index, row in enumerate(rows or [], start=1):
		item_code = row.get("item_code")
		warehouse = row.get("warehouse")
		if not item_code or not warehouse:
			continue
		previous = get_previous_sle(
			{
				"item_code": item_code,
				"warehouse": warehouse,
				"posting_date": posting_date,
				"posting_time": posting_time or "00:00:00",
			}
		)
		qty_after = flt((previous or {}).get("qty_after_transaction"))
		if qty_after >= 0:
			continue
		voucher_type = (previous or {}).get("voucher_type")
		voucher_no = (previous or {}).get("voucher_no")
		item_name = frappe.db.get_value("Item", item_code, "item_name") if item_code else None
		blocks.append(
			{
				"idx": row.get("idx") or index,
				"item_code": item_code,
				"item_name": item_name,
				"warehouse": warehouse,
				"qty_after": qty_after,
				"posting_date": (previous or {}).get("posting_date"),
				"posting_time": (previous or {}).get("posting_time"),
				"voucher_type": voucher_type,
				"voucher_no": voucher_no,
				"voucher_missing": bool(
					voucher_type and voucher_no and not frappe.db.exists(voucher_type, voucher_no)
				),
				"target_qty": row.get("qty"),
			}
		)
	return blocks


def detail_lines(blocks):
	lines = []
	for block in blocks:
		lines.extend(_lines_for_block(block))
	return lines


def headline(blocks):
	parts = [escape_html(_headline_for_block(block)) for block in blocks]
	return "<br>".join(parts)


def _item_label(block):
	if block.get("item_name"):
		return f"{block['item_code']} ({block['item_name']})"
	return block["item_code"]


def _when(block):
	return f"{formatdate(block.get('posting_date'))} {format_time(block.get('posting_time'))}"


def _lines_for_block(block):
	when = _when(block)
	needed = abs(flt(block["qty_after"]))
	lines = [
		_(
			"Fila {0}: {1} en {2} tiene saldo de libro {3} al {4}."
		).format(
			block["idx"],
			_item_label(block),
			block["warehouse"],
			format(flt(block["qty_after"]), "f").rstrip("0").rstrip("."),
			when,
		)
	]
	if block.get("voucher_type") and block.get("voucher_no"):
		if block.get("voucher_missing"):
			lines.append(
				_(
					"Ese saldo lo dejó {0} {1}. El documento ya no existe; solo quedó el movimiento de stock."
				).format(block["voucher_type"], block["voucher_no"])
			)
		else:
			lines.append(
				_("Ese saldo lo dejó {0} {1}.").format(block["voucher_type"], block["voucher_no"])
			)
	target = block.get("target_qty")
	if target is not None and target != "":
		lines.append(
			_(
				"La conciliación indica un conteo de {0}. Con el libro en negativo, el envío se rechaza antes de tomar ese conteo como saldo nuevo."
			).format(target)
		)
	else:
		lines.append(
			_(
				"Con el libro en negativo, el envío se rechaza antes de tomar el conteo como saldo nuevo."
			)
		)
	lines.append(
		_(
			"Registre una entrada de inventario de al menos {0} unidades con fecha y hora anteriores al {1}. Después concilie de nuevo si el conteo físico no coincide con el saldo corregido."
		).format(format(needed, "f").rstrip("0").rstrip("."), when)
	)
	return lines


def _headline_for_block(block):
	when = _when(block)
	needed = format(abs(flt(block["qty_after"])), "f").rstrip("0").rstrip(".")
	return _(
		"Fila {0}: {1} en {2} tiene saldo de libro {3} al {4}. Registre una entrada de al menos {5} unidades antes de esa hora."
	).format(
		block["idx"],
		_item_label(block),
		block["warehouse"],
		format(flt(block["qty_after"]), "f").rstrip("0").rstrip("."),
		when,
		needed,
	)
