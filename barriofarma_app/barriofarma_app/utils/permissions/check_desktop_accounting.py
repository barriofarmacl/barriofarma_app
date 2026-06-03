# -*- coding: utf-8 -*-
import frappe
from barriofarma_app.barriofarma_app.utils.permissions.desktop_icon_policy import (
	get_hidden_desktop_icons,
	get_profile_name_for_user,
)
from frappe.desk.doctype.desktop_icon.desktop_icon import get_desktop_icons, clear_desktop_icons_cache
from frappe.boot import get_bootinfo


def check_desktop_accounting():
	for email in [
		"eduardo.araya@barriofarma.cl",
		"karla.carmona@barriofarma.cl",
		"jimena.araya@barriofarma.cl",
		"natalia.araya@barriofarma.cl",
		"daniela.araya@barriofarma.cl",
	]:
		if not frappe.db.exists("User", email):
			continue
		frappe.set_user(email)
		clear_desktop_icons_cache(email)
		icons = sorted(i.label for i in get_desktop_icons(bootinfo=get_bootinfo()))
		print(
			email,
			"profile=",
			get_profile_name_for_user(email),
			"Accounting hidden=",
			"Accounting" in get_hidden_desktop_icons(email),
			"desktop=",
			icons,
		)
