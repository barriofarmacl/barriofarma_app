# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests integracion API catalogo terreno — issue whiteboard #75.

Cubre escenarios S3, S5, S6, S7 del spec pos-sales-order-terreno.
S1/S2/S4: cubiertos en tests frontend (Fase 5).
S8: flujo nativo make_purchase_order ERPNext (sin test en este modulo).
S9: verificacion negativa por revision de diff (no test automatizado).
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from barriofarma_app.barriofarma_app.api.catalogo_terreno import (
	create_sales_order_from_cart,
	get_post_login_path,
	list_catalog_items,
	search_customers,
)
from barriofarma_app.barriofarma_app.test_setup import (
	create_test_customer,
	create_test_item,
	create_test_warehouse,
	ensure_minimum_masters,
	get_test_company,
)
from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
	setup_permissions_for_role,
)
from barriofarma_app.barriofarma_app.utils.permissions.setup_roles import create_custom_roles
from barriofarma_app.barriofarma_app.tests.integration.test_epic8_story82_role_authorization import (
	create_test_user_with_role,
)


class TestCatalogoTerrenoApi(FrappeTestCase):
	ROLE = "Vendedor Terreno"

	def setUp(self):
		frappe.set_user("Administrator")
		ensure_minimum_masters()
		create_custom_roles()
		if not frappe.db.exists("Role", self.ROLE):
			frappe.get_doc(
				{
					"doctype": "Role",
					"role_name": self.ROLE,
					"desk_access": 0,
					"is_custom": 1,
				}
			).insert(ignore_permissions=True)
		setup_permissions_for_role(self.ROLE, use_extended_strategy=True)
		frappe.clear_cache()
		self._cleanup = []
		self.company = get_test_company()
		self.warehouse = create_test_warehouse(
			f"Almacen Catalogo Terreno {frappe.generate_hash(length=4)}",
			company=self.company,
		).name
		self._track("Warehouse", self.warehouse)

	def tearDown(self):
		frappe.set_user("Administrator")
		for name, doctype in reversed(self._cleanup):
			try:
				if frappe.db.exists(doctype, name):
					doc = frappe.get_doc(doctype, name)
					if getattr(doc, "docstatus", 0) == 1:
						doc.cancel()
					frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			except Exception:
				pass
		frappe.db.commit()

	def _track(self, doctype, name):
		self._cleanup.append((name, doctype))

	def _create_vendedor(self, username):
		user = create_test_user_with_role(username, self.ROLE)
		setup_permissions_for_role(self.ROLE, use_extended_strategy=True)
		frappe.clear_cache()
		return user.name

	def _ensure_price_list(self):
		pl_name = "Standard Selling"
		if not frappe.db.exists("Price List", pl_name):
			pl = frappe.get_doc(
				{
					"doctype": "Price List",
					"price_list_name": pl_name,
					"currency": frappe.db.get_value("Company", self.company, "default_currency")
					or "CLP",
					"selling": 1,
					"enabled": 1,
				}
			)
			pl.insert(ignore_permissions=True)
			self._track("Price List", pl.name)
			return pl.name
		return pl_name

	def _create_item_with_price(self, suffix, price_list, rate=1000):
		item = create_test_item(
			item_code=f"TEST-CAT-{suffix}",
			custom_dispensing_type="Venta Libre",
		)
		self._track("Item", item.name)
		if not frappe.db.exists(
			"Item Price",
			{"item_code": item.name, "price_list": price_list},
		):
			ip = frappe.get_doc(
				{
					"doctype": "Item Price",
					"item_code": item.name,
					"price_list": price_list,
					"price_list_rate": rate,
				}
			)
			ip.insert(ignore_permissions=True)
			self._track("Item Price", ip.name)
		return item.name

	def test_s3_list_catalog_without_pos_profile(self):
		"""S3: catalogo responde sin POS Profile ni POS Opening Entry."""
		user_a = self._create_vendedor("vendedor_cat_a")
		price_list = self._ensure_price_list()
		item_code = self._create_item_with_price("S3", price_list)

		frappe.set_user(user_a)
		result = list_catalog_items(price_list=price_list, search_term="TEST-CAT-S3")
		self.assertTrue(result)
		codes = {row["item_code"] for row in result}
		self.assertIn(item_code, codes)

	def _ensure_sales_tax_template(self):
		template_name = "IVA Ventas Catalogo Terreno"
		company = self.company
		if frappe.db.exists("Sales Taxes and Charges Template", template_name):
			return template_name

		account = frappe.db.get_value(
			"Account",
			{"company": company, "account_type": "Tax", "disabled": 0},
			"name",
		)
		if not account:
			account = frappe.db.get_value(
				"Account",
				{"company": company, "disabled": 0, "is_group": 0},
				"name",
			)
		if not account:
			self.skipTest("No hay cuenta contable para plantilla de impuestos en tests")

		template = frappe.get_doc(
			{
				"doctype": "Sales Taxes and Charges Template",
				"title": template_name,
				"company": company,
				"taxes": [
					{
						"charge_type": "On Net Total",
						"account_head": account,
						"description": "IVA",
						"rate": 19,
					}
				],
			}
		)
		template.insert(ignore_permissions=True)
		self._track("Sales Taxes and Charges Template", template.name)
		return template.name

	def _ensure_sales_tax_rule(self, template_name):
		existing = frappe.db.get_value(
			"Tax Rule",
			{
				"tax_type": "Sales",
				"company": self.company,
				"sales_tax_template": template_name,
			},
			"name",
		)
		if existing:
			return existing

		rule = frappe.get_doc(
			{
				"doctype": "Tax Rule",
				"tax_type": "Sales",
				"company": self.company,
				"sales_tax_template": template_name,
				"priority": 1,
			}
		)
		rule.insert(ignore_permissions=True)
		self._track("Tax Rule", rule.name)
		return rule.name

	def test_s5_create_sales_order_defaults(self):
		"""S5: delivery_date, taxes_and_charges y sales_team resueltos."""
		user_a = self._create_vendedor("vendedor_cat_b")
		price_list = self._ensure_price_list()
		item_code = self._create_item_with_price("S5", price_list)
		tax_template = self._ensure_sales_tax_template()
		self._ensure_sales_tax_rule(tax_template)
		customer = create_test_customer("Cliente Institucional S5")
		self._track("Customer", customer.name)

		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Vendedor",
				"last_name": "S5",
				"employee_name": "Vendedor S5",
				"company": self.company,
				"status": "Active",
				"user_id": user_a,
				"date_of_birth": "1990-01-01",
				"date_of_joining": nowdate(),
				"gender": "Male",
			}
		)
		employee.insert(ignore_permissions=True)
		self._track("Employee", employee.name)

		sp_name = f"Vendedor S5 {frappe.generate_hash(length=4)}"
		sales_person = frappe.get_doc(
			{
				"doctype": "Sales Person",
				"sales_person_name": sp_name,
				"employee": employee.name,
				"enabled": 1,
				"is_group": 0,
			}
		)
		sales_person.insert(ignore_permissions=True)
		self._track("Sales Person", sales_person.name)

		frappe.set_user(user_a)
		response = create_sales_order_from_cart(
			customer=customer.name,
			items=[{"item_code": item_code, "qty": 2, "rate": 1000}],
			price_list=price_list,
		)
		self.assertTrue(response.get("name"))
		so = frappe.get_doc("Sales Order", response["name"])
		self.assertEqual(str(so.delivery_date), str(add_days(nowdate(), 7)))
		self.assertTrue(so.taxes_and_charges)
		self.assertEqual(so.owner, user_a)
		self.assertEqual(len(so.sales_team), 1)
		self.assertEqual(so.sales_team[0].sales_person, sales_person.name)
		self._track("Sales Order", so.name)

	def test_s6_sales_order_if_owner_isolation(self):
		"""S6: vendedor A no lee Sales Order de vendedor B."""
		user_a = self._create_vendedor("vendedor_cat_c")
		user_b = self._create_vendedor("vendedor_cat_d")
		price_list = self._ensure_price_list()
		item_code = self._create_item_with_price("S6", price_list)
		customer = create_test_customer("Cliente Institucional S6")
		self._track("Customer", customer.name)

		frappe.set_user(user_b)
		response_b = create_sales_order_from_cart(
			customer=customer.name,
			items=[{"item_code": item_code, "qty": 1, "rate": 1000}],
			price_list=price_list,
		)
		so_b = response_b["name"]
		self._track("Sales Order", so_b)

		frappe.set_user(user_a)
		self.assertFalse(frappe.has_permission("Sales Order", "read", so_b))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("Sales Order", so_b, check_permission=True)

	def test_s7_search_customers_created_by_other_user(self):
		"""S7: busqueda amplia de Customer sin if_owner."""
		user_a = self._create_vendedor("vendedor_cat_e")
		customer = create_test_customer("Institucional Compartido S7")
		self._track("Customer", customer.name)

		frappe.set_user(user_a)
		results = search_customers(search_term="Institucional Compartido S7")
		names = {row["name"] for row in results}
		self.assertIn(customer.name, names)

	def test_post_login_path_vendedor_terreno_to_catalogo(self):
		"""Vendedor Terreno sin desk_access redirige al catalogo SPA."""
		user = self._create_vendedor("vendedor_cat_redirect")
		frappe.set_user(user)
		self.assertEqual(get_post_login_path(), "/inicio/catalogo")

	def test_post_login_path_desk_user_to_app(self):
		"""Usuario con rol de desk_access sigue yendo a /app."""
		user = create_test_user_with_role("auxiliar_redirect", "Auxiliar")
		frappe.set_user(user.name)
		self.assertEqual(get_post_login_path(), "/app")
