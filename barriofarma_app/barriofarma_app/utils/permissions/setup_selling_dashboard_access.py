# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tablero estándar ``Selling`` (Ventas): gráficos tipo Report y tarjetas numéricas.

Frappe filtra por ``get_allowed_report_names()`` (roles en Report) y por lectura del
``document_type`` / ``ref_doctype``. Perfiles operativos sin ``Sales User`` no ven gráficos.
"""

import frappe

SELLING_DASHBOARD_REPORTS = (
	"Item-wise Sales History",
	"Sales Order Analysis",
	"Delivery Note Trends",
	"Sales Order Trends",
)

OPERATIVE_ROLES = ("Farmacéutico", "Auxiliar", "Informática")


def _ensure_report_roles(report_name: str, roles: tuple[str, ...]) -> list[str]:
	"""Añade roles en Report.roles sin guardar el Report (válido con developer_mode=0)."""
	if not frappe.db.exists("Report", report_name):
		return []

	added = []
	existing = set(
		frappe.get_all(
			"Has Role",
			filters={
				"parent": report_name,
				"parenttype": "Report",
				"parentfield": "roles",
			},
			pluck="role",
		)
	)

	for role in roles:
		if role not in existing:
			frappe.get_doc(
				{
					"doctype": "Has Role",
					"parent": report_name,
					"parenttype": "Report",
					"parentfield": "roles",
					"role": role,
				}
			).insert(ignore_permissions=True)
			added.append(role)

	return added


def setup_selling_dashboard_reports():
	"""Idempotente: permite reportes del tablero Ventas a Farmacéutico y Auxiliar."""
	all_added = []
	for report_name in SELLING_DASHBOARD_REPORTS:
		added = _ensure_report_roles(report_name, OPERATIVE_ROLES)
		if added:
			all_added.append(f"{report_name}: {', '.join(added)}")

	if all_added:
		frappe.db.commit()
		# Invalidar caché de reportes permitidos en boot
		for user in frappe.get_all("User", filters={"enabled": 1}, pluck="name"):
			frappe.cache.hdel("has_role:Report", user)

	return all_added
