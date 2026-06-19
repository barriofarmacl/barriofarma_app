# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Reportes de inventario y tablero ``Stock`` para perfiles operativos.

Los reportes de existencias usan ``ref_doctype`` = Stock Ledger Entry; además hace falta
asignar roles en el DocType Report (``get_allowed_report_names``).
"""

import frappe

from barriofarma_app.barriofarma_app.utils.permissions.setup_selling_dashboard_access import (
	_ensure_report_roles,
)

OPERATIVE_ROLES = ("Farmacéutico", "Auxiliar", "Informática")

# Existencias y trazabilidad (farmacia)
STOCK_INVENTORY_REPORTS = (
	"Stock Balance",
	"Stock Ledger",
	"Warehouse Wise Stock Balance",
	"Batch Item Expiry Status",
	"Batch-Wise Balance History",
	"Item Shortage Report",  # ES: Reporte de productos con stock bajo
)

# Gráficos del tablero Stock estándar (tipo Report)
STOCK_DASHBOARD_REPORTS = (
	"Item Shortage Summary",
	"Stock Ageing",
)


def setup_stock_inventory_reports():
	"""Reportes de existencias / lote para Farmacéutico y Auxiliar."""
	all_added = []
	for report_name in STOCK_INVENTORY_REPORTS:
		added = _ensure_report_roles(report_name, OPERATIVE_ROLES)
		if added:
			all_added.append(f"{report_name}: {', '.join(added)}")

	if all_added:
		frappe.db.commit()
		_clear_report_role_cache()

	return all_added


def setup_stock_dashboard_reports():
	"""Gráficos del tablero Almacén."""
	all_added = []
	for report_name in STOCK_DASHBOARD_REPORTS:
		added = _ensure_report_roles(report_name, OPERATIVE_ROLES)
		if added:
			all_added.append(f"{report_name}: {', '.join(added)}")

	if all_added:
		frappe.db.commit()
		_clear_report_role_cache()

	return all_added


def apply_stock_dashboard_access():
	"""Ejecutar inventario + tablero Stock."""
	inv = setup_stock_inventory_reports()
	dash = setup_stock_dashboard_reports()
	return inv + dash


def _clear_report_role_cache():
	for user in frappe.get_all("User", filters={"enabled": 1}, pluck="name"):
		frappe.cache.hdel("has_role:Report", user)
