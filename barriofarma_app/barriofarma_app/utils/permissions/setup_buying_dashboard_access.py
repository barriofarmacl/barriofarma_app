# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tablero ``Buying`` (Compras): gráficos tipo Report y workspace ``Purchase Order Trends``.

Los Dashboard Chart con ``chart_type=Report`` exigen el reporte en ``get_allowed_report_names()``.
ERPNext asigna esos reportes a roles estándar (Purchase User, …); Farmacéutico no los trae.

Farmacéutico (operación) e Informática (mantenedor plataforma): Auxiliar no debe ver
gráficos de compras (sigue sin roles en estos reportes).
"""

import frappe

from barriofarma_app.barriofarma_app.utils.permissions.setup_selling_dashboard_access import (
	_ensure_report_roles,
)

# Gráficos del Dashboard ``Buying`` y del workspace Compras (línea de tendencias)
BUYING_DASHBOARD_REPORTS = (
	"Purchase Order Trends",
	"Purchase Order Analysis",
	"Purchase Receipt Trends",  # Dashboard Chart ``Top Suppliers``
)

BUYING_DASHBOARD_ROLES = ("Farmacéutico", "Informática")


def setup_buying_dashboard_reports():
	"""Idempotente: reportes del tablero Compras para Farmacéutico e Informática."""
	all_added = []
	for report_name in BUYING_DASHBOARD_REPORTS:
		added = _ensure_report_roles(report_name, BUYING_DASHBOARD_ROLES)
		if added:
			all_added.append(f"{report_name}: {', '.join(added)}")

	if all_added:
		frappe.db.commit()
		_clear_report_role_cache()

	return all_added


def _clear_report_role_cache():
	for user in frappe.get_all("User", filters={"enabled": 1}, pluck="name"):
		frappe.cache.hdel("has_role:Report", user)
