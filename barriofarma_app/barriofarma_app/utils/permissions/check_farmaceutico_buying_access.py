# -*- coding: utf-8 -*-
"""Verifica tablero Compras y sección Productos y Precios para Farmacéutico."""

import json

import frappe
from frappe.desk.desktop import get_desktop_page


PRODUCTS_PRICING = (
	"Item",
	"Item Price",
	"Price List",
	"Product Bundle",
	"Item Group",
	"Promotional Scheme",
	"Pricing Rule",
)

BUYING_TOOLS = (
	"Material Request",
	"Purchase Order",
	"Purchase Invoice",
	"Request for Quotation",
	"Supplier Quotation",
)


def check_farmaceutico_buying_access(email="natalia.araya@barriofarma.cl"):
	if not frappe.db.exists("User", email):
		print(email, "SKIP (no user)")
		return

	frappe.set_user(email)
	frappe.get_user().build_permissions()

	print("=== Permisos read (Productos y Precios + Compras) ===")
	for dt in PRODUCTS_PRICING + BUYING_TOOLS:
		print(email, dt, "read=", frappe.has_permission(dt, "read"))

	print("=== Workspace Buying — enlaces visibles ===")
	page = get_desktop_page(json.dumps({"name": "Buying", "title": "Buying"}))
	for card in page.get("cards", {}).get("items", []):
		label = card.get("label", "")
		if label in ("Items & Pricing", "Productos y Precios", "Buying", "Compras", "Supplier", "Proveedor", "Settings", "Configuración"):
			links = [lnk.get("label") for lnk in card.get("links", [])]
			print(f"  [{label}]", ", ".join(links) if links else "(vacío)")
