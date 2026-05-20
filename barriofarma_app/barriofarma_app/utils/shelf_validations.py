# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Validaciones transversales de estantes para movimientos de stock en bodega.

Regla de proyecto (Issue #58): ningún movimiento físico de stock puede guardarse
sin estante asociado en el almacén correspondiente, y todo almacén operativo
debe tener al menos un estante activo.
"""

import frappe
from frappe import _
from frappe.utils import flt


def count_active_shelves(warehouse):
	if not warehouse:
		return 0
	return frappe.db.count("Shelf", {"warehouse": warehouse, "disabled": 0})


def assert_warehouse_has_active_shelves(warehouse, *, context=None, title=None):
	"""El almacén debe tener al menos un estante activo antes de mover stock."""
	if not warehouse:
		return
	if count_active_shelves(warehouse) > 0:
		return
	ctx = f" {context}" if context else ""
	frappe.throw(
		_(
			"El almacén {0} no tiene estantes activos.{1} "
			"Configure al menos un estante en este almacén antes de registrar movimientos de stock."
		).format(frappe.bold(warehouse), ctx),
		title=title or _("Almacén sin estantes"),
	)


def assert_shelf_exists_and_active(shelf, row_idx, *, field_label=None):
	field_label = field_label or _("Estante")
	if not shelf:
		frappe.throw(
			_("Fila #{0}: debe indicar el {1}.").format(row_idx, field_label),
			title=_("Estante obligatorio"),
		)
	if not frappe.db.exists("Shelf", shelf):
		frappe.throw(
			_("Fila #{0}: el estante {1} no existe.").format(row_idx, frappe.bold(shelf)),
			title=_("Estante inválido"),
		)
	if frappe.db.get_value("Shelf", shelf, "disabled"):
		frappe.throw(
			_("Fila #{0}: el estante {1} está deshabilitado.").format(row_idx, frappe.bold(shelf)),
			title=_("Estante deshabilitado"),
		)


def assert_shelf_matches_warehouse(shelf, warehouse, row_idx, *, field_label=None):
	if not shelf or not warehouse:
		return
	field_label = field_label or _("Estante")
	shelf_wh = frappe.db.get_value("Shelf", shelf, "warehouse")
	if shelf_wh and shelf_wh != warehouse:
		frappe.throw(
			_(
				"Fila #{0}: el {1} {2} pertenece al almacén {3}, "
				"pero la línea usa el almacén {4}."
			).format(
				row_idx,
				field_label,
				frappe.bold(shelf),
				frappe.bold(shelf_wh),
				frappe.bold(warehouse),
			),
			title=_("Estante y almacén no coinciden"),
		)


def validate_inbound_shelf_line(
	row_idx,
	item_code,
	warehouse,
	shelf,
	*,
	field_label=None,
	missing_shelf_message=None,
):
	"""
	Línea que ingresa stock a un almacén: exige almacén con estantes y estante destino válido.
	Usado en Purchase Receipt, Stock Reconciliation y salida destino de Stock Entry.
	"""
	if not warehouse:
		return

	assert_warehouse_has_active_shelves(
		warehouse,
		context=_("Recepción o ingreso de productos en este almacén."),
	)

	if not shelf:
		msg = missing_shelf_message or _(
			"Fila #{0}: debe indicar el estante donde ubicar el producto {1} "
			"en el almacén {2}."
		).format(row_idx, frappe.bold(item_code or "-"), frappe.bold(warehouse))
		frappe.throw(msg, title=_("Estante obligatorio"))

	field_label = field_label or _("Estante")
	assert_shelf_exists_and_active(shelf, row_idx, field_label=field_label)
	assert_shelf_matches_warehouse(shelf, warehouse, row_idx, field_label=field_label)


def validate_outbound_shelf_line(
	row_idx,
	item_code,
	warehouse,
	shelf,
	*,
	field_label=None,
):
	"""Línea que sale de un almacén: exige almacén con estantes y estante origen válido."""
	if not warehouse:
		return

	assert_warehouse_has_active_shelves(
		warehouse,
		context=_("Salida de productos desde este almacén."),
	)

	if not shelf:
		frappe.throw(
			_(
				"Fila #{0}: debe indicar el <strong>Estante Origen</strong> del producto {1} "
				"en el almacén {2}."
			).format(row_idx, frappe.bold(item_code or "-"), frappe.bold(warehouse)),
			title=_("Estante origen obligatorio"),
		)

	field_label = field_label or _("Estante origen")
	assert_shelf_exists_and_active(shelf, row_idx, field_label=field_label)
	assert_shelf_matches_warehouse(shelf, warehouse, row_idx, field_label=field_label)


def validate_stock_entry_item_shelves(item, row_idx):
	"""
	Regla obligatoria por línea de Stock Entry:
	- s_warehouse -> custom_from_shelf
	- t_warehouse -> custom_to_shelf
	"""
	if not item.get("item_code"):
		return

	if not frappe.db.get_value("Item", item.item_code, "is_stock_item"):
		return

	qty = flt(item.qty)
	if qty <= 0:
		return

	s_warehouse = item.get("s_warehouse")
	t_warehouse = item.get("t_warehouse")
	from_shelf = item.get("custom_from_shelf")
	to_shelf = item.get("custom_to_shelf")

	if s_warehouse:
		validate_outbound_shelf_line(
			row_idx,
			item.item_code,
			s_warehouse,
			from_shelf,
		)

	if t_warehouse:
		validate_inbound_shelf_line(
			row_idx,
			item.item_code,
			t_warehouse,
			to_shelf,
			field_label=_("Estante destino"),
			missing_shelf_message=_(
				"Fila #{0}: debe indicar el <strong>Estante Destino</strong> del producto {1} "
				"en el almacén {2}."
			).format(row_idx, frappe.bold(item.item_code), frappe.bold(t_warehouse)),
		)
