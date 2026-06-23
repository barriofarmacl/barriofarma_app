# -*- coding: utf-8 -*-
"""Verificación rápida de permisos Almacén/Compras para perfiles operativos."""
import frappe
from frappe.desk.desk_page import get

from barriofarma_app.barriofarma_app.utils.permissions.frappe_v16_compat import (
	get_allowed_report_names,
)


STOCK_REPORTS = (
	"Stock Balance",
	"Stock Ledger",
	"Warehouse Wise Stock Balance",
)

WAREHOUSE_READ_DOCTYPES = (
	"Buying Settings",
	"Stock Settings",
	"Purchase Receipt",
	"Purchase Order",
	"Item",
	"Warehouse",
	"Supplier",
	"Batch",
	"UOM",
	"Purchase Taxes and Charges Template",
	"Shelf",
	"Stock Entry",
	"Shelf Movement",
	"Stock Ledger Entry",
)


def check_warehouse_access():
	for email in (
		"daniela.araya@barriofarma.cl",
		"natalia.araya@barriofarma.cl",
	):
		if not frappe.db.exists("User", email):
			print(email, "SKIP")
			continue
		frappe.set_user(email)
		print("---", email, "---")
		for dt in WAREHOUSE_READ_DOCTYPES:
			print(" ", dt, "read=", frappe.has_permission(dt, "read"))
		print(
			" Purchase Receipt submit=",
			frappe.has_permission("Purchase Receipt", "submit"),
		)
		print(
			" Stock Entry submit=",
			frappe.has_permission("Stock Entry", "submit"),
		)
		reports = get_allowed_report_names()
		for r in STOCK_REPORTS:
			print(" ", r, "allowed=", r in reports)
		try:
			get("stock-balance")
			print(" stock-balance page= OK")
		except frappe.PermissionError:
			print(" stock-balance page= DENIED")
		print(" Stock Entry write=", frappe.has_permission("Stock Entry", "write"))
