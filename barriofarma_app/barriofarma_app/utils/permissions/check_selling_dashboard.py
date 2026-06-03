# -*- coding: utf-8 -*-
import frappe
from frappe.boot import get_allowed_report_names
from frappe.desk.doctype.dashboard.dashboard import get_permitted_charts, get_permitted_cards


def check_selling_dashboard():
	for email in (
		"daniela.araya@barriofarma.cl",
		"natalia.araya@barriofarma.cl",
	):
		if not frappe.db.exists("User", email):
			continue
		frappe.set_user(email)
		charts = get_permitted_charts("Selling")
		cards = get_permitted_cards("Selling")
		reports = get_allowed_report_names()
		print(
			email,
			"charts=",
			len(charts),
			"cards=",
			len(cards),
			"selling_reports=",
			sum(
				1
				for r in (
					"Item-wise Sales History",
					"Sales Order Analysis",
					"Delivery Note Trends",
					"Sales Order Trends",
				)
				if r in reports
			),
		)
