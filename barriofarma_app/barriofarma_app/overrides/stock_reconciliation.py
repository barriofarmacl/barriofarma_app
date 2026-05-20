# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Override de Stock Reconciliation para exigir estante por línea al cargar inventario físico.

Issue #58 / UAT 2.0: conciliación de inventario como entrada de stock real por estante.
"""

from barriofarma_app.barriofarma_app.utils.shelf_movement_submit import insert_and_submit_shelf_movement
from barriofarma_app.barriofarma_app.utils.shelf_validations import validate_inbound_shelf_line
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import (
	StockReconciliation as ERPNextStockReconciliation,
)


class StockReconciliation(ERPNextStockReconciliation):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.stock.doctype.stock_reconciliation_item.stock_reconciliation_item import StockReconciliationItem
		from frappe.types import DF

		amended_from: DF.Link | None
		company: DF.Link
		cost_center: DF.Link | None
		difference_amount: DF.Currency
		expense_account: DF.Link | None
		items: DF.Table[StockReconciliationItem]
		naming_series: DF.Literal["MAT-RECO-.YYYY.-"]
		posting_date: DF.Date
		posting_time: DF.Time
		purpose: DF.Literal["", "Opening Stock", "Stock Reconciliation"]
		scan_barcode: DF.Data | None
		scan_mode: DF.Check
		set_posting_time: DF.Check
		set_warehouse: DF.Link | None
	# end: auto-generated types
	def validate(self):
		super().validate()
		self.validate_shelf_required()

	def on_submit(self):
		super().on_submit()
		self.create_shelf_movements_from_reconciliation()
		self.ensure_item_shelf_locations()

	def validate_shelf_required(self):
		if not self.items:
			return

		for row in self.items:
			validate_inbound_shelf_line(
				row.idx,
				row.item_code,
				row.warehouse,
				row.get("shelf"),
				field_label=_("Estante"),
				missing_shelf_message=_(
					"Fila #{0}: debe indicar el <strong>Estante</strong> donde está el producto "
					"{1}. La conciliación de inventario exige ubicación física por línea."
				).format(row.idx, frappe.bold(row.item_code)),
			)
			self._validate_shelf_item_compatibility(row.get("shelf"), row.item_code, row.idx)

	def _validate_shelf_item_compatibility(self, shelf_name, item_code, row_idx):
		if not item_code or not frappe.db.exists("Item", item_code):
			return

		shelf_type = frappe.db.get_value("Shelf", shelf_name, "shelf_type")
		item_doc = frappe.get_doc("Item", item_code)

		if shelf_type == "Refrigerado" and not item_doc.get("custom_requires_refrigeration"):
			frappe.throw(
				_(
					"Fila #{0}: el estante {1} es Refrigerado; el producto {2} no requiere refrigeración."
				).format(row_idx, frappe.bold(shelf_name), frappe.bold(item_code)),
				title=_("Incompatibilidad estante-producto"),
			)

		if shelf_type == "Controlado":
			control_level = item_doc.get("custom_control_level")
			if not control_level or control_level == "None":
				frappe.throw(
					_(
						"Fila #{0}: el estante {1} es Controlado; el producto {2} no tiene nivel de control."
					).format(row_idx, frappe.bold(shelf_name), frappe.bold(item_code)),
					title=_("Incompatibilidad estante-producto"),
				)

	def create_shelf_movements_from_reconciliation(self):
		if not self.items:
			return

		for row in self.items:
			shelf = row.get("shelf")
			if not shelf:
				continue

			qty_delta = flt(row.quantity_difference)
			if not qty_delta:
				qty_delta = flt(row.qty) - flt(row.current_qty)

			if qty_delta == 0:
				continue

			if qty_delta > 0:
				movement_type = "Recepción"
			else:
				movement_type = "Ajuste"
				qty_delta = abs(qty_delta)

			self._create_shelf_movement(
				movement_type=movement_type,
				shelf=shelf,
				item_code=row.item_code,
				quantity=qty_delta,
				row_idx=row.idx,
			)

	def ensure_item_shelf_locations(self):
		for row in self.items:
			shelf = row.get("shelf")
			item_code = row.get("item_code")
			if not shelf or not item_code or not frappe.db.exists("Item", item_code):
				continue

			item_doc = frappe.get_doc("Item", item_code)
			if not hasattr(item_doc, "custom_shelf_locations"):
				continue

			existing = {r.shelf for r in (item_doc.custom_shelf_locations or []) if r.shelf}
			if shelf in existing:
				continue

			item_doc.append(
				"custom_shelf_locations",
				{
					"shelf": shelf,
					"preferred_location": 0 if existing else 1,
					"quantity": flt(row.qty),
				},
			)
			try:
				item_doc.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(
					message=f"Error al vincular item {item_code} al estante {shelf}: {e}",
					title="Stock Reconciliation — Item Shelf Location",
				)

	def _create_shelf_movement(self, movement_type, shelf, item_code, quantity, row_idx):
		try:
			movement = frappe.get_doc(
				{
					"doctype": "Shelf Movement",
					"movement_type": movement_type,
					"shelf": shelf,
					"item": item_code,
					"quantity": quantity,
					"movement_date": self.posting_date,
					"reference_doctype": "Stock Reconciliation",
					"reference_name": self.name,
					"notes": _(
						"Movimiento automático desde Reconciliación de inventarios {0} (fila {1})"
					).format(self.name, row_idx),
				}
			)
			insert_and_submit_shelf_movement(movement)
		except Exception as e:
			frappe.log_error(
				message=f"Error al crear Shelf Movement desde {self.name}: {e}",
				title="Error en Shelf Movement (Stock Reconciliation)",
			)
