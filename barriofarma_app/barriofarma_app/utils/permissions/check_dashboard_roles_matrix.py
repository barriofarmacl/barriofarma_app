# -*- coding: utf-8 -*-
# Smoke: matriz permisos paneles BF — barriofarma-number-cards-platform

import frappe

USERS = (
	("eduardo.araya@barriofarma.cl", "Eduardo — Perfil Informática"),
	("natalia.araya@barriofarma.cl", "Natalia — Perfil Farmacéutico"),
	("daniela.araya@barriofarma.cl", "Daniela — Perfil Auxiliar"),
)

CHECKS = (
	("Workspace", "read"),
	("Workspace", "create"),
	("Workspace", "write"),
	("Number Card", "read"),
	("Number Card", "write"),
	("Dashboard Chart", "read"),
	("Dashboard Chart", "write"),
	("Report", "read"),
)


def check_dashboard_roles_matrix():
	"""Print effective Desk permissions for workspace/KPI maintainers vs operativos."""
	from frappe.desk.doctype.workspace.workspace import is_workspace_manager

	for email, label in USERS:
		if not frappe.db.exists("User", email):
			print(f"{label}: SKIP (user missing)")
			continue
		frappe.set_user(email)
		frappe.get_user().build_permissions()
		roles = sorted(set(frappe.get_roles()) - {"All", "Guest"})
		print(f"\n{label}")
		print(f"  roles: {', '.join(roles)}")
		print(f"  is_workspace_manager: {is_workspace_manager()}")
		for doctype, ptype in CHECKS:
			ok = frappe.has_permission(doctype, ptype)
			print(f"  {doctype} {ptype}: {ok}")

	frappe.set_user("Administrator")
