# -*- coding: utf-8 -*-
import frappe
from frappe.desk.doctype.desktop_icon.desktop_icon import get_desktop_icons, clear_desktop_icons_cache
from frappe.boot import get_bootinfo


def audit_uat_menus():
	for email in ["natalia.araya@barriofarma.cl", "daniela.araya@barriofarma.cl"]:
		clear_desktop_icons_cache(email)
		frappe.set_user(email)
		u = frappe.get_doc("User", email)
		roles = frappe.get_roles(email)
		blocked = sorted(u.get_blocked_modules())
		boot = get_bootinfo()
		icons = get_desktop_icons(user=email, bootinfo=boot)
		labels = sorted(i.get("label") for i in icons)
		print(f"\n=== {email} ===")
		print("roles:", roles)
		print("Setup blocked:", "Setup" in blocked)
		print("Accounts blocked:", "Accounts" in blocked)
		print("DESKTOP:", labels)
		for ws in ("buying", "selling", "stock", "organization"):
			try:
				items = boot.workspace_sidebar_item.get(ws, {}).get("items", [])
				links = [
					f"{i.get('label')} -> {i.get('link_to')}"
					for i in items
					if i.get("type") == "Link"
				]
				print(f"SIDEBAR {ws} ({len(links)}):", links)
			except KeyError:
				print(f"SIDEBAR {ws}: (not in boot)")
