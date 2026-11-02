# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# Issue: whiteboard #88

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from barriofarma_app.barriofarma_app.api.pos_past_orders import (
	_apply_pos_profile,
	get_past_order_list,
)
from barriofarma_app.barriofarma_app.utils.setup.warehouse_fulfillment_constants import (
	POS_PROFILE_REPARTO_NAME,
)
from erpnext.selling.page.point_of_sale.point_of_sale import get_invoice_filters


class TestPosPastOrderFilter(FrappeTestCase):
	ROJAS_PROFILE = "Caja Rojas 1"

	def test_apply_pos_profile_adds_filter_for_pos_invoice(self):
		base = get_invoice_filters("POS Invoice", "Draft")
		filtered = _apply_pos_profile(base, "POS Invoice", self.ROJAS_PROFILE)
		self.assertEqual(filtered["pos_profile"], self.ROJAS_PROFILE)

	def test_apply_pos_profile_ignores_other_doctypes(self):
		base = {"docstatus": 0}
		filtered = _apply_pos_profile(base, "Delivery Note", self.ROJAS_PROFILE)
		self.assertNotIn("pos_profile", filtered)

	def test_past_orders_scoped_to_active_profile(self):
		if not frappe.db.exists("POS Profile", self.ROJAS_PROFILE):
			self.skipTest(f"POS Profile {self.ROJAS_PROFILE} not on site")
		if not frappe.db.exists("POS Profile", POS_PROFILE_REPARTO_NAME):
			self.skipTest(f"POS Profile {POS_PROFILE_REPARTO_NAME} not on site")

		rojas_invoice = frappe.db.get_value(
			"POS Invoice",
			{"pos_profile": self.ROJAS_PROFILE, "docstatus": 0},
			"name",
		)
		if not rojas_invoice:
			self.skipTest("No draft POS Invoice for Caja Rojas 1 on site")

		reparto_results = get_past_order_list(
			search_term="", status="Draft", pos_profile=POS_PROFILE_REPARTO_NAME
		)
		reparto_names = {row["name"] for row in reparto_results}
		self.assertNotIn(rojas_invoice, reparto_names)

		rojas_results = get_past_order_list(
			search_term="", status="Draft", pos_profile=self.ROJAS_PROFILE
		)
		rojas_names = {row["name"] for row in rojas_results}
		self.assertIn(rojas_invoice, rojas_names)
