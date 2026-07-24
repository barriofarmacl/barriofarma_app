# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Stock Reconciliation con productos Venta con Receta Retenida (whiteboard #78 PR3).

Perfil canónico RR: lote + caducidad, sin número de serie (SLA farmacia = trazabilidad por lote).

Usa unittest.TestCase (no FrappeTestCase) para evitar preload de test records
ERPNext / BootStrapTestData sobre _Test Company incompleto tras restore PROD.
"""

import unittest

import frappe
from frappe.utils import add_days, cint, today

from barriofarma_app.barriofarma_app.test_setup import (
	create_test_item,
	create_test_shelf,
	create_test_warehouse,
	ensure_minimum_masters,
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


def _make_batch(item_code, batch_id=None, expiry_days=365):
	batch_id = batch_id or f"LOT-{frappe.generate_hash(length=8)}"
	doc = frappe.get_doc(
		{
			"doctype": "Batch",
			"item": item_code,
			"batch_id": batch_id,
			"expiry_date": add_days(today(), expiry_days),
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc


class TestStockReconciliationRecetaRetenida(unittest.TestCase):
	"""Whiteboard #78 PR3 — RR solo lote (sin serie)."""

	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		ensure_minimum_masters()

	def setUp(self):
		frappe.set_user("Administrator")
		ensure_minimum_masters()
		self.company = get_test_company()
		self.test_items = []
		self.test_warehouses = []
		self.test_shelves = []
		self.test_batches = []
		self.test_reconciliations = []

		self.warehouse = create_test_warehouse(f"TEST-WH-SR-RR-{frappe.generate_hash(length=6)}")
		self.test_warehouses.append(self.warehouse.name)
		self.shelf = create_test_shelf(
			shelf_name=f"Estante SR RR {frappe.generate_hash(length=4)}",
			warehouse=self.warehouse.name,
			location_code=f"SRRR-{frappe.generate_hash(length=4)}",
		)
		self.test_shelves.append(self.shelf.name)

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
		for name in self.test_batches:
			try:
				if frappe.db.exists("Batch", name):
					frappe.delete_doc("Batch", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		for name in self.test_items:
			try:
				if frappe.db.exists("Item", name):
					frappe.delete_doc("Item", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		for name in self.test_shelves:
			try:
				if frappe.db.exists("Shelf", name):
					frappe.delete_doc("Shelf", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		for name in self.test_warehouses:
			try:
				if frappe.db.exists("Warehouse", name):
					frappe.delete_doc("Warehouse", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		frappe.db.commit()

	def _rr_item(self, **kwargs):
		defaults = {
			"item_code": f"TEST-RR-SR-{frappe.generate_hash(length=6)}",
			"item_name": "RR SR Test",
			"custom_dispensing_type": "Venta con Receta Retenida",
			"custom_sanitary_registration": f"ISP-SR-{frappe.generate_hash(length=4)}",
			"has_batch_no": 1,
			"has_expiry_date": 1,
			"create_new_batch": 0,
			"has_serial_no": 0,
		}
		defaults.update(kwargs)
		defaults["has_serial_no"] = 0
		defaults.setdefault("batch_number_series", "")
		defaults.setdefault("serial_no_series", "")
		item = create_test_item(**defaults)
		frappe.db.set_value(
			"Item",
			item.name,
			{
				"create_new_batch": cint(defaults.get("create_new_batch", 0)),
				"has_serial_no": 0,
				"batch_number_series": defaults.get("batch_number_series") or "",
				"serial_no_series": "",
			},
		)
		item.reload()
		self.test_items.append(item.name)
		return item

	def _sr_doc(self, item_code, qty=5, valuation_rate=100, **item_row):
		row = {
			"item_code": item_code,
			"warehouse": self.warehouse.name,
			"shelf": self.shelf.name,
			"qty": qty,
			"valuation_rate": valuation_rate,
			"use_serial_batch_fields": 1,
		}
		row.update(item_row)
		return frappe.get_doc(
			{
				"doctype": "Stock Reconciliation",
				"company": self.company,
				"purpose": "Stock Reconciliation",
				"expense_account": _expense_account(self.company),
				"posting_date": today(),
				"items": [row],
			}
		)

	def test_rr_batch_item_requires_batch_on_reconciliation(self):
		"""Receta Retenida con lote y create_new_batch=0: SR sin batch_no falla."""
		item = self._rr_item(has_batch_no=1, create_new_batch=0)
		doc = self._sr_doc(item.name, batch_no=None)
		with self.assertRaises((frappe.ValidationError, frappe.MandatoryError)):
			doc.insert(ignore_permissions=True)

	def test_rr_batch_item_reconciles_when_batch_provided(self):
		"""Con batch_no informado, SR de Receta Retenida submit OK."""
		item = self._rr_item(has_batch_no=1, create_new_batch=0)
		batch = _make_batch(item.name)
		self.test_batches.append(batch.name)

		doc = self._sr_doc(item.name, qty=7, batch_no=batch.name)
		doc.insert(ignore_permissions=True)
		doc.submit()
		frappe.db.commit()
		self.test_reconciliations.append(doc.name)

		doc.reload()
		self.assertEqual(doc.docstatus, 1)
		self.assertEqual(doc.items[0].batch_no, batch.name)

	def test_venta_libre_still_reconciles_with_shelf(self):
		"""Venta Libre sigue reconciliable (sin restricción nueva a Receta Retenida)."""
		item = create_test_item(
			item_code=f"TEST-VL-SR-{frappe.generate_hash(length=6)}",
			custom_dispensing_type="Venta Libre",
			has_batch_no=0,
			has_serial_no=0,
		)
		self.test_items.append(item.name)

		doc = self._sr_doc(item.name, qty=12)
		doc.items[0].use_serial_batch_fields = 0
		doc.items[0].batch_no = None
		doc.items[0].serial_no = None
		doc.insert(ignore_permissions=True)
		doc.submit()
		frappe.db.commit()
		self.test_reconciliations.append(doc.name)

		doc.reload()
		self.assertEqual(doc.docstatus, 1)
		self.assertEqual(cint(frappe.db.get_value("Item", item.name, "has_batch_no")), 0)
