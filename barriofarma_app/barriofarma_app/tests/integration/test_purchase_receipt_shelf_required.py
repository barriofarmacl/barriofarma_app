# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Tests: estante destino obligatorio en Purchase Receipt (Issue #58)."""

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


class TestPurchaseReceiptShelfRequired(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_minimum_masters()
		self._cleanup = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for name, doctype in reversed(self._cleanup):
			try:
				if frappe.db.exists(doctype, name):
					doc = frappe.get_doc(doctype, name)
					if doc.docstatus == 1:
						doc.cancel()
					frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			except Exception:
				pass
		frappe.db.commit()

	def _append(self, doctype, name):
		self._cleanup.append((name, doctype))

	def test_pr_requires_shelf_on_submit(self):
		wh = create_test_warehouse(f"TEST-WH-PR-{frappe.generate_hash(length=6)}")
		self._append("Warehouse", wh.name)
		shelf = create_test_shelf(
			shelf_name="Estante PR Test",
			warehouse=wh.name,
			location_code=f"PR-{frappe.generate_hash(length=4)}",
		)
		self._append("Shelf", shelf.name)
		item = create_test_item(
			item_code=f"TEST-PR-SHELF-{frappe.generate_hash(length=6)}",
			custom_dispensing_type="Venta Libre",
		)
		self._append("Item", item.name)

		pr = frappe.get_doc(
			{
				"doctype": "Purchase Receipt",
				"company": get_test_company(),
				"supplier": frappe.db.get_value("Supplier", {}, "name"),
				"set_warehouse": wh.name,
				"posting_date": today(),
				"items": [
					{
						"item_code": item.name,
						"qty": 5,
						"warehouse": wh.name,
						"rate": 100,
					}
				],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			pr.insert(ignore_permissions=True)

	def test_pr_fails_when_warehouse_has_no_shelves(self):
		wh = create_test_warehouse(f"TEST-WH-NOSHELF-{frappe.generate_hash(length=6)}")
		self._append("Warehouse", wh.name)
		other_wh = create_test_warehouse(f"TEST-WH-OTHER-{frappe.generate_hash(length=6)}")
		self._append("Warehouse", other_wh.name)
		shelf_other = create_test_shelf(
			shelf_name="Estante otro almacén",
			warehouse=other_wh.name,
			location_code=f"OTH-{frappe.generate_hash(length=4)}",
		)
		self._append("Shelf", shelf_other.name)
		item = create_test_item(
			item_code=f"TEST-PR-NOSHELF-{frappe.generate_hash(length=6)}",
			custom_dispensing_type="Venta Libre",
		)
		self._append("Item", item.name)

		pr = frappe.get_doc(
			{
				"doctype": "Purchase Receipt",
				"company": get_test_company(),
				"supplier": frappe.db.get_value("Supplier", {}, "name"),
				"set_warehouse": wh.name,
				"posting_date": today(),
				"items": [
					{
						"item_code": item.name,
						"qty": 5,
						"warehouse": wh.name,
						"rate": 100,
						"custom_to_shelf": shelf_other.name,
					}
				],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			pr.insert(ignore_permissions=True)
