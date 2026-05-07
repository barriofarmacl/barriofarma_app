# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""API POS para mostrar distribución de stock por estante."""

from __future__ import annotations

import frappe
from frappe import _
from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability


@frappe.whitelist()
def get_item_shelf_summary(item_code: str, warehouse: str) -> dict:
	"""Retorna estantes configurados del item para un warehouse en formato POS."""
	item_code = (item_code or "").strip()
	warehouse = (warehouse or "").strip()

	if not item_code or not warehouse:
		return {"summary": "", "shelves": [], "warehouse_qty": 0}

	# Usar la misma fuente que POS para evitar diferencias visuales con "Cantidad Disponible".
	try:
		pos_availability = get_stock_availability(item_code=item_code, warehouse=warehouse)
		warehouse_qty = float(pos_availability[0] or 0)
	except Exception:
		warehouse_qty = (
			frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0
		)

	shelves = frappe.db.sql(
		"""
		SELECT
			isl.shelf,
			s.shelf_name,
			COALESCE(isl.quantity, 0) AS qty,
			COALESCE(isl.preferred_location, 0) AS preferred_location
		FROM `tabItem Shelf Location` isl
		INNER JOIN `tabShelf` s ON s.name = isl.shelf
		WHERE isl.parent = %(item_code)s
			AND s.warehouse = %(warehouse)s
			AND COALESCE(s.disabled, 0) = 0
		ORDER BY COALESCE(isl.preferred_location, 0) DESC, s.shelf_name ASC
		""",
		{"item_code": item_code, "warehouse": warehouse},
		as_dict=True,
	)

	# Stock dinámico por shelf desde movimientos (si existen)
	movement_rows = frappe.db.sql(
		"""
		SELECT t.shelf, SUM(t.delta_qty) AS qty
		FROM (
			-- Origen / normal
			SELECT
				sm.shelf AS shelf,
				CASE
					WHEN sm.movement_type = 'Recepción' THEN sm.quantity
					WHEN sm.movement_type = 'Transferencia' THEN -sm.quantity
					WHEN sm.movement_type IN ('Venta', 'Ajuste') THEN -sm.quantity
					ELSE 0
				END AS delta_qty
			FROM `tabShelf Movement` sm
			INNER JOIN `tabShelf` s ON s.name = sm.shelf
			WHERE sm.item = %(item_code)s
				AND s.warehouse = %(warehouse)s
				AND sm.docstatus = 1

			UNION ALL

			-- Destino de transferencia
			SELECT
				sm.to_shelf AS shelf,
				sm.quantity AS delta_qty
			FROM `tabShelf Movement` sm
			INNER JOIN `tabShelf` s_to ON s_to.name = sm.to_shelf
			WHERE sm.item = %(item_code)s
				AND sm.movement_type = 'Transferencia'
				AND sm.to_shelf IS NOT NULL
				AND s_to.warehouse = %(warehouse)s
				AND sm.docstatus = 1
		) t
		WHERE t.shelf IS NOT NULL
		GROUP BY t.shelf
		""",
		{"item_code": item_code, "warehouse": warehouse},
		as_dict=True,
	)
	movement_qty_by_shelf = {r.get("shelf"): float(r.get("qty") or 0) for r in movement_rows}

	parts: list[str] = []
	only_one_shelf = len(shelves) == 1
	for row in shelves:
		label = (row.get("shelf_name") or row.get("shelf") or "").strip()
		configured_qty = float(row.get("qty") or 0)
		movement_qty = movement_qty_by_shelf.get(row.get("shelf"))

		# Regla operativa dev:
		# - Si hay un solo estante para ese item+warehouse, usar Bin como fuente de verdad.
		# - Si hay múltiples estantes, usar movimientos (o cantidad configurada).
		if only_one_shelf:
			display_qty = float(warehouse_qty or 0)
		elif movement_qty is not None:
			display_qty = movement_qty
		elif configured_qty > 0:
			display_qty = configured_qty
		else:
			display_qty = configured_qty

		row["qty"] = display_qty
		if not label:
			continue
		parts.append(f"{label}: {display_qty:g}")

	summary = " | ".join(parts)
	if not summary and shelves:
		summary = _("Estantes configurados sin cantidad por estante")

	return {
		"summary": summary,
		"shelves": shelves,
		"warehouse_qty": warehouse_qty,
	}

