# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# Issue: whiteboard #88 — Recent Orders must be scoped to active POS Profile

"""Filter POS Recent Orders by active pos_profile (multi-channel POS)."""

from __future__ import annotations

import frappe

from erpnext.selling.page.point_of_sale.point_of_sale import (
	add_doctype_to_results,
	get_invoice_filters,
	order_results_by_posting_date,
)


def _apply_pos_profile(filters: dict, doctype: str, pos_profile: str | None) -> dict:
	if pos_profile and doctype in ("POS Invoice", "Sales Invoice"):
		filters = dict(filters)
		filters["pos_profile"] = pos_profile
	return filters


@frappe.whitelist()
def get_past_order_list(search_term, status, limit=20, pos_profile=None):
	"""Same as ERPNext get_past_order_list but scoped to the active POS Profile when provided."""
	fields = [
		"name",
		"grand_total",
		"currency",
		"customer",
		"customer_name",
		"posting_time",
		"posting_date",
	]
	invoice_list = []

	if search_term and status:
		pos_filters = _apply_pos_profile(
			get_invoice_filters("POS Invoice", status), "POS Invoice", pos_profile
		)
		pos_invoices_by_customer = frappe.db.get_list(
			"POS Invoice",
			filters=pos_filters,
			or_filters={
				"customer_name": ["like", f"%{search_term}%"],
				"customer": ["like", f"%{search_term}%"],
			},
			fields=fields,
			page_length=limit,
		)
		pos_invoices_by_name = frappe.db.get_list(
			"POS Invoice",
			filters=_apply_pos_profile(
				get_invoice_filters("POS Invoice", status, name=search_term),
				"POS Invoice",
				pos_profile,
			),
			fields=fields,
			page_length=limit,
		)
		pos_invoice_list = add_doctype_to_results(
			"POS Invoice", pos_invoices_by_customer + pos_invoices_by_name
		)

		si_filters = _apply_pos_profile(
			get_invoice_filters("Sales Invoice", status), "Sales Invoice", pos_profile
		)
		sales_invoices_by_customer = frappe.db.get_list(
			"Sales Invoice",
			filters=si_filters,
			or_filters={
				"customer_name": ["like", f"%{search_term}%"],
				"customer": ["like", f"%{search_term}%"],
			},
			fields=fields,
			page_length=limit,
		)
		sales_invoices_by_name = frappe.db.get_list(
			"Sales Invoice",
			filters=_apply_pos_profile(
				get_invoice_filters("Sales Invoice", status, name=search_term),
				"Sales Invoice",
				pos_profile,
			),
			fields=fields,
			page_length=limit,
		)
		sales_invoice_list = add_doctype_to_results(
			"Sales Invoice", sales_invoices_by_customer + sales_invoices_by_name
		)

	elif status:
		pos_invoice_list = frappe.db.get_list(
			"POS Invoice",
			filters=_apply_pos_profile(
				get_invoice_filters("POS Invoice", status), "POS Invoice", pos_profile
			),
			fields=fields,
			page_length=limit,
		)
		pos_invoice_list = add_doctype_to_results("POS Invoice", pos_invoice_list)

		sales_invoice_list = frappe.db.get_list(
			"Sales Invoice",
			filters=_apply_pos_profile(
				get_invoice_filters("Sales Invoice", status), "Sales Invoice", pos_profile
			),
			fields=fields,
			page_length=limit,
		)
		sales_invoice_list = add_doctype_to_results("Sales Invoice", sales_invoice_list)
	else:
		pos_invoice_list = []
		sales_invoice_list = []

	invoice_list = order_results_by_posting_date([*pos_invoice_list, *sales_invoice_list])
	return invoice_list
