# -*- coding: utf-8 -*-
# Issue: barriofarma-number-cards-platform

import frappe
from frappe.tests.utils import FrappeTestCase

from barriofarma_app.barriofarma_app.utils.dashboard.dashboard_constants import (
	CH_BF_TICKETS_DIA,
	CH_BF_VENTAS_HORA,
	LEGACY_CH_TICKETS_HORA,
	NC_BF_BOLETA,
	NC_BF_ITEMS,
	NC_BF_OC,
	NC_BF_TICKETS_ULTIMA_HORA,
	NC_BF_VENTAS_ULTIMA_HORA,
	REPORT_BF_VENTAS_HORA,
)
from barriofarma_app.barriofarma_app.utils.dashboard.barriofarma_dashboard_widgets import (
	setup_barriofarma_dashboard,
)
from barriofarma_app.barriofarma_app.utils.dashboard.embed_workspace_content import (
	content_references_widget,
	parse_workspace_content,
)

MAINTAINER_EMAIL = "eduardo.araya@barriofarma.cl"


class TestBarriofarmaPosDashboard(FrappeTestCase):
	def setUp(self):
		setup_barriofarma_dashboard()

	def test_bf_widgets_exist_and_are_custom(self):
		for doctype, name in (
			("Number Card", NC_BF_VENTAS_ULTIMA_HORA),
			("Number Card", NC_BF_TICKETS_ULTIMA_HORA),
			("Number Card", NC_BF_BOLETA),
			("Dashboard Chart", CH_BF_VENTAS_HORA),
			("Dashboard Chart", CH_BF_TICKETS_DIA),
			("Number Card", NC_BF_OC),
			("Number Card", NC_BF_ITEMS),
		):
			self.assertTrue(frappe.db.exists(doctype, name), f"Missing {doctype} {name}")
			row = frappe.db.get_value(
				doctype, name, ["is_standard", "module"], as_dict=True
			)
			self.assertEqual(row.is_standard, 0)
			self.assertEqual(row.module, "Barriofarma App")

		self.assertTrue(
			frappe.db.exists("Report", REPORT_BF_VENTAS_HORA),
			f"Missing Report {REPORT_BF_VENTAS_HORA}",
		)
		self.assertFalse(
			frappe.db.exists("Dashboard Chart", LEGACY_CH_TICKETS_HORA),
			"Legacy BF Tickets Hora chart should be retired",
		)

	def test_selling_workspace_embeds_pos_widgets(self):
		content = parse_workspace_content(frappe.db.get_value("Workspace", "Selling", "content"))
		for block_type, name in (
			("number_card", NC_BF_VENTAS_ULTIMA_HORA),
			("number_card", NC_BF_TICKETS_ULTIMA_HORA),
			("number_card", NC_BF_BOLETA),
			("chart", CH_BF_VENTAS_HORA),
			("chart", CH_BF_TICKETS_DIA),
		):
			self.assertTrue(
				content_references_widget(content, block_type, name),
				f"Selling missing {block_type} {name}",
			)

	def test_maintainer_can_write_number_card(self):
		if not frappe.db.exists("User", MAINTAINER_EMAIL):
			self.skipTest(f"{MAINTAINER_EMAIL} not in site")
		frappe.set_user(MAINTAINER_EMAIL)
		self.assertTrue(frappe.has_permission("Number Card", "write"))
		frappe.set_user("Administrator")

	def test_maintainer_can_write_user_and_workspace(self):
		if not frappe.db.exists("User", MAINTAINER_EMAIL):
			self.skipTest(f"{MAINTAINER_EMAIL} not in site")
		frappe.set_user(MAINTAINER_EMAIL)
		roles = set(frappe.get_roles())
		self.assertIn("System Manager", roles)
		self.assertIn("Workspace Manager", roles)
		self.assertTrue(frappe.has_permission("User", "write"))
		self.assertTrue(frappe.has_permission("Workspace", "write"))
		frappe.set_user("Administrator")
