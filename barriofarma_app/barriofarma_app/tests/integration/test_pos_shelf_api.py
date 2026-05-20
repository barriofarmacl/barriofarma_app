# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Tests API POS estantes — fallback desde Shelf Movement."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from barriofarma_app.barriofarma_app.api.pos_shelf import get_item_shelf_summary
from barriofarma_app.barriofarma_app.test_setup import (
	create_test_item,
	create_test_shelf,
	create_test_warehouse,
	ensure_minimum_masters,
	get_test_company,
)
from barriofarma_app.barriofarma_app.utils.shelf_movement_submit import insert_and_submit_shelf_movement


class TestPosShelfApi(FrappeTestCase):
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
					if getattr(doc, "docstatus", 0) == 1:
						doc.cancel()
					frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			except Exception:
				pass
		frappe.db.commit()

	def _track(self, doctype, name):
		self._cleanup.append((name, doctype))

	def test_summary_from_shelf_movement_without_item_shelf_location(self):
		wh = create_test_warehouse(f"TEST-WH-POS-{frappe.generate_hash(length=6)}")
		self._track("Warehouse", wh.name)
		shelf = create_test_shelf(
			shelf_name="POS M1",
			warehouse=wh.name,
			location_code=f"POS-{frappe.generate_hash(length=4)}",
		)
		self._track("Shelf", shelf.name)
		item = create_test_item(
			item_code=f"TEST-POS-SHELF-{frappe.generate_hash(length=6)}",
			custom_dispensing_type="Venta Libre",
		)
		self._track("Item", item.name)

		movement = frappe.get_doc(
			{
				"doctype": "Shelf Movement",
				"movement_type": "Recepción",
				"shelf": shelf.name,
				"item": item.name,
				"quantity": 12,
				"movement_date": today(),
			}
		)
		insert_and_submit_shelf_movement(movement)
		self._track("Shelf Movement", movement.name)

		result = get_item_shelf_summary(item.name, wh.name)
		self.assertIn("POS M1", result.get("summary") or "")
		self.assertTrue(result.get("shelves"))
