# -*- coding: utf-8 -*-
import frappe
from frappe.boot import get_sidebar_items
from frappe.desk.desk_page import get
from frappe.desk.desktop import get_workspace_sidebar_items


def check_pos_page_access():
	restrict_domain = frappe.db.get_value("Page", "point-of-sale", "restrict_to_domain")
	print("Page point-of-sale restrict_to_domain=", repr(restrict_domain or ""))

	for email in (
		"daniela.araya@barriofarma.cl",
		"natalia.araya@barriofarma.cl",
	):
		if not frappe.db.exists("User", email):
			print(email, "SKIP (no user)")
			continue
		frappe.set_user(email)
		frappe.get_user().build_permissions()
		try:
			get("point-of-sale")
			print(email, "OK point-of-sale")
		except frappe.PermissionError:
			print(email, "DENIED point-of-sale")
			continue

		ws = get_workspace_sidebar_items()
		sidebar = get_sidebar_items([d.name for d in ws.get("pages")])
		pos_links = [
			i
			for i in sidebar.get("selling", {}).get("items", [])
			if i.get("link_to") == "point-of-sale"
		]
		print(email, "sidebar POS link=", bool(pos_links))

		for dt in (
			"Stock Settings",
			"POS Settings",
			"Account",
			"Cost Center",
			"Mode of Payment",
			"UOM",
			"Territory",
			"Customer Group",
			"Currency",
		):
			ok = frappe.has_permission(dt, "read")
			print(email, dt, "read=", ok)
