# -*- coding: utf-8 -*-
# whiteboard #80 follow-up: map_docs 403 — override must be Frappe-whitelisted.

import unittest

import frappe

from barriofarma_app.barriofarma_app.overrides.purchase_receipt import make_purchase_invoice


class TestMakePurchaseInvoiceWhitelist(unittest.TestCase):
	def test_make_purchase_invoice_is_whitelisted(self):
		self.assertIn(
			make_purchase_invoice,
			frappe.whitelisted,
			"overrides.purchase_receipt.make_purchase_invoice must be @frappe.whitelist() "
			"so frappe.model.mapper.map_docs can create PI from PR",
		)
