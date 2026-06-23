# -*- coding: utf-8 -*-
import frappe
from frappe.desk.doctype.dashboard.dashboard import get_permitted_charts, get_permitted_cards

from barriofarma_app.barriofarma_app.utils.permissions.frappe_v16_compat import (
	get_allowed_report_names,
)
from frappe.desk.desktop import get_desktop_page
import json


BUYING_REPORTS = (
	"Purchase Order Trends",
	"Purchase Order Analysis",
	"Purchase Receipt Trends",
	"Material Request Analysis",
	"Purchase Analytics",
	"Item-wise Purchase History",
)


def check_buying_dashboard():
	for email in (
		"eduardo.araya@barriofarma.cl",
		"daniela.araya@barriofarma.cl",
		"natalia.araya@barriofarma.cl",
	):
		if not frappe.db.exists("User", email):
			continue
		frappe.set_user(email)
		frappe.get_user().build_permissions()
		reports = get_allowed_report_names()
		charts_dash = get_permitted_charts("Buying")
		cards_dash = get_permitted_cards("Buying")
		page = get_desktop_page(json.dumps({"name": "Buying", "title": "Buying"}))
		ws_charts = len(page.get("charts", {}).get("items", []))
		ws_cards = len(page.get("number_cards", {}).get("items", []))
		print(
			email,
			"dashboard charts=",
			len(charts_dash),
			"dashboard cards=",
			len(cards_dash),
			"workspace charts=",
			ws_charts,
			"workspace cards=",
			ws_cards,
			"buying_reports=",
			sum(1 for r in BUYING_REPORTS if r in reports),
		)
		for r in BUYING_REPORTS:
			if r not in reports:
				print("  missing report:", r)
