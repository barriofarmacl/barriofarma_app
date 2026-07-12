# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""API catalogo + carrito para vendedores en terreno (issue whiteboard #75)."""

from __future__ import annotations

import logging

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, nowdate, parse_json

from erpnext.accounts.party import get_party_details

from barriofarma_app.barriofarma_app.test_setup import get_test_company

logger = logging.getLogger(__name__)

ROLE_VENDEDOR_TERRENO = "Vendedor Terreno"
DEFAULT_DELIVERY_DAYS = 7
POST_LOGIN_CATALOGO_PATH = "/inicio/catalogo"
POST_LOGIN_DESK_PATH = "/app"


def _ensure_catalogo_access():
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Inicie sesion para continuar"), frappe.AuthenticationError)

	roles = set(frappe.get_roles())
	if ROLE_VENDEDOR_TERRENO not in roles and "Administrator" not in roles:
		frappe.throw(
			_("No tiene permiso para acceder al catalogo de terreno"),
			frappe.PermissionError,
		)


def _get_default_company() -> str:
	company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)
	if company:
		return company
	try:
		return get_test_company()
	except Exception:
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			frappe.throw(_("No hay Company configurada en el sitio"))
		return company


def _get_default_warehouse(company: str) -> str | None:
	"""Almacen por defecto para lineas de Sales Order (items de stock exigen warehouse)."""
	warehouse = frappe.db.get_value(
		"Warehouse",
		{"company": company, "is_group": 0, "disabled": 0},
		"name",
		order_by="creation asc",
	)
	if warehouse:
		return warehouse

	global_wh = frappe.db.get_single_value("Stock Settings", "default_warehouse")
	if global_wh and frappe.db.get_value("Warehouse", global_wh, "company") == company:
		return global_wh

	return None


def _get_sales_person_for_user(user: str | None = None) -> str | None:
	"""Resolve Sales Person via Employee.user_id (ERPNext v16 has no direct User link on Sales Person)."""
	user = user or frappe.session.user
	employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
	if not employee:
		logger.warning(
			"catalogo_terreno: usuario %s sin Employee vinculado; sales_team omitido",
			user,
		)
		return None

	sales_person = frappe.db.get_value(
		"Sales Person",
		{"employee": employee, "enabled": 1},
		"name",
	)
	if not sales_person:
		logger.warning(
			"catalogo_terreno: Employee %s sin Sales Person habilitado; sales_team omitido",
			employee,
		)
	return sales_person


def _list_catalog_items_impl(
	search_term=None,
	item_group=None,
	price_list=None,
	start=0,
	page_length=20,
):
	if not price_list:
		frappe.throw(_("price_list es obligatorio"))

	filters = {"disabled": 0, "is_sales_item": 1}
	if item_group:
		filters["item_group"] = item_group

	or_filters = None
	if search_term and str(search_term).strip():
		term = f"%{search_term.strip()}%"
		or_filters = [["item_code", "like", term], ["item_name", "like", term]]

	items = frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name as item_code",
			"item_name",
			"item_group",
			"image",
			"stock_uom as uom",
			"custom_control_level",
		],
		limit_start=cint(start),
		limit_page_length=cint(page_length),
		order_by="item_name asc",
	)

	if not items:
		return []

	item_codes = [row["item_code"] for row in items]
	price_rows = frappe.get_all(
		"Item Price",
		filters={"price_list": price_list, "item_code": ["in", item_codes]},
		fields=["item_code", "price_list_rate"],
	)
	price_map = {row.item_code: flt(row.price_list_rate) for row in price_rows}

	stock_rows = frappe.db.sql(
		"""
		SELECT item_code, SUM(actual_qty) AS stock_qty
		FROM `tabBin`
		WHERE item_code IN %(items)s
		GROUP BY item_code
		""",
		{"items": item_codes},
		as_dict=True,
	)
	stock_map = {row.item_code: max(0.0, flt(row.stock_qty)) for row in stock_rows}

	result = []
	for row in items:
		code = row["item_code"]
		if code not in price_map:
			continue
		result.append(
			{
				"item_code": code,
				"item_name": row["item_name"],
				"item_group": row["item_group"],
				"image": row.get("image"),
				"uom": row["uom"],
				"rate": price_map[code],
				"stock_qty": stock_map.get(code, 0),
				"custom_control_level": row.get("custom_control_level") or "",
			}
		)
	return result


def _search_customers_impl(search_term=None, limit=20):
	filters = {}
	or_filters = None
	if search_term and str(search_term).strip():
		term = f"%{search_term.strip()}%"
		or_filters = [["name", "like", term], ["customer_name", "like", term]]

	return frappe.get_all(
		"Customer",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "customer_name"],
		limit_page_length=cint(limit),
		order_by="customer_name asc",
	)


def _create_sales_order_from_cart_impl(
	customer,
	items,
	delivery_date=None,
	price_list=None,
):
	if isinstance(items, str):
		items = parse_json(items)
	if not customer:
		frappe.throw(_("customer es obligatorio"))
	if not items:
		frappe.throw(_("items no puede estar vacio"))

	company = _get_default_company()
	party_details = get_party_details(
		party=customer,
		party_type="Customer",
		company=company,
		doctype="Sales Order",
		price_list=price_list,
	)

	so = frappe.new_doc("Sales Order")
	so.company = company
	so.customer = customer
	so.transaction_date = nowdate()
	so.delivery_date = delivery_date or add_days(nowdate(), DEFAULT_DELIVERY_DAYS)
	so.selling_price_list = price_list or party_details.get("selling_price_list")

	default_warehouse = _get_default_warehouse(company)
	if default_warehouse:
		so.set_warehouse = default_warehouse

	for field in (
		"taxes_and_charges",
		"customer_address",
		"shipping_address_name",
		"contact_person",
		"currency",
		"payment_terms_template",
	):
		if party_details.get(field):
			so.set(field, party_details.get(field))

	if not so.taxes_and_charges:
		default_tax_template = frappe.db.get_value(
			"Sales Taxes and Charges Template",
			{"company": company},
			"name",
			order_by="creation asc",
		)
		if default_tax_template:
			so.taxes_and_charges = default_tax_template

	for row in items:
		item_code = row.get("item_code")
		if not item_code:
			frappe.throw(_("Cada item debe incluir item_code"))
		qty = flt(row.get("qty"))
		if qty <= 0:
			frappe.throw(_("Cantidad invalida para {0}").format(item_code))
		item_row = {
			"item_code": item_code,
			"qty": qty,
			"delivery_date": so.delivery_date,
		}
		if row.get("rate") is not None:
			item_row["rate"] = flt(row.get("rate"))
		so.append("items", item_row)

	sales_person = _get_sales_person_for_user()
	if sales_person:
		so.set("sales_team", [])
		so.append(
			"sales_team",
			{"sales_person": sales_person, "allocated_percentage": 100},
		)

	so.run_method("set_missing_values")
	so.insert()

	return {"name": so.name, "status": so.status}


def _resolve_post_login_path_for_user(user: str | None = None) -> str:
	"""Vendedor Terreno sin ningun rol con desk_access va al catalogo SPA; resto a Desk."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return POST_LOGIN_DESK_PATH

	roles = [role for role in frappe.get_roles(user) if role not in ("All", "Guest")]
	has_vendedor_terreno = ROLE_VENDEDOR_TERRENO in roles
	has_desk_access = any(
		cint(frappe.db.get_value("Role", role, "desk_access"))
		for role in roles
		if frappe.db.exists("Role", role)
	)

	if has_vendedor_terreno and not has_desk_access:
		return POST_LOGIN_CATALOGO_PATH
	return POST_LOGIN_DESK_PATH


@frappe.whitelist()
def get_post_login_path():
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Inicie sesion para continuar"), frappe.AuthenticationError)
	return _resolve_post_login_path_for_user()


@frappe.whitelist()
def list_catalog_items(
	search_term=None,
	item_group=None,
	price_list=None,
	start=0,
	page_length=20,
):
	_ensure_catalogo_access()
	return _list_catalog_items_impl(
		search_term=search_term,
		item_group=item_group,
		price_list=price_list,
		start=start,
		page_length=page_length,
	)


@frappe.whitelist()
def list_item_groups():
	_ensure_catalogo_access()
	return frappe.get_all(
		"Item Group",
		filters={"is_group": 0},
		fields=["name"],
		order_by="name asc",
	)


@frappe.whitelist()
def search_customers(search_term=None):
	_ensure_catalogo_access()
	return _search_customers_impl(search_term=search_term)


@frappe.whitelist()
def create_sales_order_from_cart(customer, items, delivery_date=None, price_list=None):
	_ensure_catalogo_access()
	return _create_sales_order_from_cart_impl(
		customer=customer,
		items=items,
		delivery_date=delivery_date,
		price_list=price_list,
	)
