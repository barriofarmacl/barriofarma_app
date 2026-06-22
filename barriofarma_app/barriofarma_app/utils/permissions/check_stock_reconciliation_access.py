# -*- coding: utf-8 -*-
import frappe

from barriofarma_app.barriofarma_app.utils.permissions.frappe_v16_compat import (
	get_sidebar_items_for_user,
)


def check_stock_reconciliation_access():
	for email in (
		"daniela.araya@barriofarma.cl",
		"natalia.araya@barriofarma.cl",
	):
		if not frappe.db.exists("User", email):
			print(email, "SKIP (no user)")
			continue
		frappe.set_user(email)
		frappe.get_user().build_permissions()
		for perm in ("read", "create", "write", "submit"):
			ok = frappe.has_permission("Stock Reconciliation", perm)
			print(email, "Stock Reconciliation", perm, "=", ok)

		sidebar = get_sidebar_items_for_user()
		links = [
			i
			for i in sidebar.get("stock", {}).get("items", [])
			if i.get("link_to") == "Stock Reconciliation"
		]
		print(email, "sidebar Stock Reconciliation link=", bool(links))
