# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
PO/PR Receta Retenida con roles reales (whiteboard #78 PR4).

Flujo:
- Farmacéutico: crea/submit Purchase Order
- Auxiliar: crea Purchase Receipt borrador (con lote + QC)
- Farmacéutico: submit Purchase Receipt

Usa unittest.TestCase para evitar BootStrap ERPNext en site con dump PROD.
"""

import unittest

import frappe
from frappe.utils import add_days, today

from barriofarma_app.barriofarma_app.test_setup import (
	create_test_batch,
	create_test_item,
	create_test_supplier,
	create_test_warehouse,
	ensure_minimum_masters,
	get_test_company,
)
from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
	setup_permissions_for_role,
)


def _normalize_user(user: str) -> str:
	if not user or user in ("Administrator", "Guest") or "@" in user:
		return user
	if frappe.db.exists("User", user):
		return user
	return f"{user}@test.barriofarma.cl"


def _create_user_with_role(username: str, role_name: str) -> str:
	email = _normalize_user(username)
	frappe.flags.in_import = True
	try:
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": username,
					"username": username,
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			frappe.db.commit()

		if not frappe.db.exists("Has Role", {"parent": email, "role": role_name}):
			frappe.get_doc(
				{
					"doctype": "Has Role",
					"parent": email,
					"parenttype": "User",
					"parentfield": "roles",
					"role": role_name,
				}
			).insert(ignore_permissions=True)
			frappe.db.commit()
	finally:
		frappe.flags.in_import = False

	frappe.clear_cache()
	return email


class TestPoPrRecetaRetenidaRoles(unittest.TestCase):
	"""Whiteboard #78 PR4."""

	def setUp(self):
		frappe.set_user("Administrator")
		ensure_minimum_masters()
		self.company = get_test_company()
		self.test_users = []
		self.test_items = []
		self.test_suppliers = []
		self.test_warehouses = []
		self.test_batches = []
		self.test_pos = []
		self.test_prs = []

		self.farm_user = _create_user_with_role(
			f"test_farm_po_{frappe.generate_hash(length=6)}", "Farmacéutico"
		)
		self.aux_user = _create_user_with_role(
			f"test_aux_pr_{frappe.generate_hash(length=6)}", "Auxiliar"
		)
		self.test_users.extend([self.farm_user, self.aux_user])

		setup_permissions_for_role("Farmacéutico", use_extended_strategy=True)
		setup_permissions_for_role("Auxiliar", use_extended_strategy=True)
		frappe.clear_cache()

		self.warehouse = create_test_warehouse(
			f"TEST-WH-POPR-{frappe.generate_hash(length=6)}",
			company=self.company,
		)
		self.test_warehouses.append(self.warehouse.name)

		self.supplier = create_test_supplier(f"SUP-POPR-{frappe.generate_hash(length=6)}")
		self.test_suppliers.append(self.supplier.name)

		self.item = create_test_item(
			item_code=f"TEST-RR-POPR-{frappe.generate_hash(length=6)}",
			item_name="RR PO/PR Test",
			custom_dispensing_type="Venta con Receta Retenida",
			custom_sanitary_registration=f"ISP-POPR-{frappe.generate_hash(length=4)}",
			has_batch_no=1,
			has_expiry_date=1,
			has_serial_no=0,
			shelf_life_in_days=9999,
		)
		self.test_items.append(self.item.name)

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in self.test_prs:
			try:
				if frappe.db.exists("Purchase Receipt", name):
					doc = frappe.get_doc("Purchase Receipt", name)
					if doc.docstatus == 1:
						doc.cancel()
					frappe.delete_doc("Purchase Receipt", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		for name in self.test_pos:
			try:
				if frappe.db.exists("Purchase Order", name):
					doc = frappe.get_doc("Purchase Order", name)
					if doc.docstatus == 1:
						doc.cancel()
					frappe.delete_doc("Purchase Order", name, force=True, ignore_permissions=True)
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
		for name in self.test_warehouses:
			try:
				if frappe.db.exists("Warehouse", name):
					frappe.db.sql("DELETE FROM `tabStock Ledger Entry` WHERE warehouse=%s", name)
					frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse=%s", name)
					for shelf in frappe.get_all("Shelf", filters={"warehouse": name}, pluck="name"):
						frappe.db.sql("DELETE FROM `tabShelf Movement` WHERE shelf=%s", shelf)
						frappe.delete_doc("Shelf", shelf, force=True, ignore_permissions=True)
					frappe.delete_doc("Warehouse", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		for name in self.test_suppliers:
			try:
				if frappe.db.exists("Supplier", name):
					frappe.delete_doc("Supplier", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		for email in self.test_users:
			try:
				if frappe.db.exists("User", email):
					frappe.delete_doc("User", email, force=True, ignore_permissions=True)
			except Exception:
				pass
		frappe.db.commit()
		frappe.clear_cache()

	def _create_po_as_farm(self, qty=5, rate=100):
		frappe.set_user(self.farm_user)
		frappe.clear_cache()
		company_currency = frappe.db.get_value("Company", self.company, "default_currency") or "CLP"
		po = frappe.get_doc(
			{
				"doctype": "Purchase Order",
				"supplier": self.supplier.name,
				"company": self.company,
				"currency": company_currency,
				"conversion_rate": 1,
				"price_list_currency": company_currency,
				"plc_conversion_rate": 1,
				"transaction_date": today(),
				"schedule_date": add_days(today(), 7),
				"items": [
					{
						"item_code": self.item.name,
						"qty": qty,
						"uom": self.item.stock_uom,
						"rate": rate,
						"schedule_date": add_days(today(), 7),
						"warehouse": self.warehouse.name,
					}
				],
			}
		)
		po.insert()
		po.submit()
		frappe.db.commit()
		self.test_pos.append(po.name)
		return po

	def _pr_draft_payload(self, po, batch_name, qty=5, rate=100):
		po_item = po.items[0].name
		return {
			"doctype": "Purchase Receipt",
			"supplier": self.supplier.name,
			"company": self.company,
			"posting_date": today(),
			"set_warehouse": self.warehouse.name,
			"items": [
				{
					"item_code": self.item.name,
					"qty": qty,
					"received_qty": qty,
					"uom": self.item.stock_uom,
					"rate": rate,
					"warehouse": self.warehouse.name,
					"purchase_order": po.name,
					"purchase_order_item": po_item,
					"batch_no": batch_name,
					"custom_qc_status": "Aceptado",
				}
			],
		}

	def test_farmaceutico_creates_and_submits_po_for_receta_retenida(self):
		"""Farm crea y confirma PO de producto Receta Retenida."""
		po = self._create_po_as_farm(qty=4)
		po.reload()
		self.assertEqual(po.docstatus, 1)
		self.assertEqual(po.items[0].item_code, self.item.name)

	def test_auxiliar_creates_pr_draft_and_farmaceutico_submits(self):
		"""Aux crea PR borrador con lote; Farm hace submit (flujo operativo)."""
		from barriofarma_app.barriofarma_app.validations.purchase_receipt_permissions import (
			validate_purchase_receipt_submit_authorization,
		)

		po = self._create_po_as_farm(qty=3)

		frappe.set_user("Administrator")
		batch = create_test_batch(
			self.item.name,
			batch_id=f"LOT-POPR-{frappe.generate_hash(length=6)}",
			expiry_date=add_days(today(), 400),
		)
		self.test_batches.append(batch.name)

		frappe.set_user(self.aux_user)
		frappe.clear_cache()
		self.assertTrue(frappe.has_permission("Purchase Receipt", "create"))
		self.assertFalse(frappe.has_permission("Purchase Receipt", "submit"))

		pr = frappe.get_doc(self._pr_draft_payload(po, batch.name, qty=3))
		pr.insert()
		frappe.db.commit()
		self.test_prs.append(pr.name)
		pr.reload()
		self.assertEqual(pr.docstatus, 0)
		self.assertEqual(pr.items[0].batch_no, batch.name)

		# Auxiliar bloqueado a nivel de regla de dominio (sin invocar submit ERPNext/SABB)
		with self.assertRaises(frappe.ValidationError):
			validate_purchase_receipt_submit_authorization(pr)

		# Farmacéutico submit OK
		frappe.set_user(self.farm_user)
		frappe.clear_cache()
		self.assertTrue(frappe.has_permission("Purchase Receipt", "submit"))
		pr = frappe.get_doc("Purchase Receipt", pr.name)
		pr.submit()
		frappe.db.commit()
		pr.reload()
		self.assertEqual(pr.docstatus, 1)

	def test_farmaceutico_cannot_create_purchase_receipt(self):
		"""Farm no inicia PR; debe fallar create."""
		po = self._create_po_as_farm(qty=2)

		frappe.set_user("Administrator")
		batch = create_test_batch(
			self.item.name,
			batch_id=f"LOT-FARM-DENY-{frappe.generate_hash(length=6)}",
			expiry_date=add_days(today(), 400),
		)
		self.test_batches.append(batch.name)

		frappe.set_user(self.farm_user)
		frappe.clear_cache()
		self.assertFalse(frappe.has_permission("Purchase Receipt", "create"))

		pr = frappe.get_doc(self._pr_draft_payload(po, batch.name, qty=2))
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			pr.insert()
