# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests de Stock Reconciliation con estante obligatorio (Issue #58).
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from barriofarma_app.barriofarma_app.test_setup import (
	ensure_minimum_masters,
	create_test_item,
	create_test_warehouse,
	create_test_shelf,
	get_test_company,
)


def _expense_account(company):
	return (
		frappe.get_cached_value("Company", company, "stock_adjustment_account")
		or frappe.db.get_value(
			"Account",
			{"account_type": "Stock Adjustment", "company": company, "is_group": 0},
			"name",
		)
	)


class TestStockReconciliationShelf(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_minimum_masters()
		self.test_items = []
		self.test_warehouses = []
		self.test_shelves = []
		self.test_reconciliations = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in self.test_reconciliations:
			try:
				if frappe.db.exists("Stock Reconciliation", name):
					doc = frappe.get_doc("Stock Reconciliation", name)
					if doc.docstatus == 1:
						doc.cancel()
					frappe.delete_doc("Stock Reconciliation", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		for item in self.test_items:
			try:
				if frappe.db.exists("Item", item):
					frappe.delete_doc("Item", item, force=True, ignore_permissions=True)
			except Exception:
				pass
		for shelf in self.test_shelves:
			try:
				if frappe.db.exists("Shelf", shelf):
					frappe.delete_doc("Shelf", shelf, force=True, ignore_permissions=True)
			except Exception:
				pass
		for wh in self.test_warehouses:
			try:
				if frappe.db.exists("Warehouse", wh):
					frappe.delete_doc("Warehouse", wh, force=True, ignore_permissions=True)
			except Exception:
				pass
		frappe.db.commit()

	def test_reconciliation_requires_shelf(self):
		warehouse = create_test_warehouse(f"TEST-WH-RECO-{frappe.generate_hash(length=6)}")
		self.test_warehouses.append(warehouse.name)
		item = create_test_item(
			item_code=f"TEST-ITEM-RECO-{frappe.generate_hash(length=6)}",
			custom_dispensing_type="Venta Libre",
		)
		self.test_items.append(item.name)
		company = get_test_company()

		doc = frappe.get_doc(
			{
				"doctype": "Stock Reconciliation",
				"company": company,
				"purpose": "Stock Reconciliation",
				"expense_account": _expense_account(company),
				"posting_date": today(),
				"items": [
					{
						"item_code": item.name,
						"warehouse": warehouse.name,
						"qty": 10,
						"valuation_rate": 100,
					}
				],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_reconciliation_with_shelf_creates_movement(self):
		warehouse = create_test_warehouse(f"TEST-WH-RECO2-{frappe.generate_hash(length=6)}")
		self.test_warehouses.append(warehouse.name)
		shelf = create_test_shelf(
			shelf_name="Estante Reco Test",
			warehouse=warehouse.name,
			location_code=f"RECO-{frappe.generate_hash(length=4)}",
		)
		self.test_shelves.append(shelf.name)
		item = create_test_item(
			item_code=f"TEST-ITEM-RECO2-{frappe.generate_hash(length=6)}",
			custom_dispensing_type="Venta Libre",
		)
		self.test_items.append(item.name)
		company = get_test_company()

		doc = frappe.get_doc(
			{
				"doctype": "Stock Reconciliation",
				"company": company,
				"purpose": "Stock Reconciliation",
				"expense_account": _expense_account(company),
				"posting_date": today(),
				"items": [
					{
						"item_code": item.name,
						"warehouse": warehouse.name,
						"shelf": shelf.name,
						"qty": 15,
						"valuation_rate": 100,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
		doc.submit()
		frappe.db.commit()
		self.test_reconciliations.append(doc.name)

		movements = frappe.get_all(
			"Shelf Movement",
			filters={
				"reference_doctype": "Stock Reconciliation",
				"reference_name": doc.name,
				"docstatus": 1,
			},
			fields=["movement_type", "quantity", "shelf"],
		)
		self.assertEqual(len(movements), 1)
		self.assertEqual(movements[0].movement_type, "Recepción")
		self.assertEqual(movements[0].quantity, 15)
		self.assertEqual(movements[0].shelf, shelf.name)
