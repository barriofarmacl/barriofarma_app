# -*- coding: utf-8 -*-
# Issue: acceso Informática a Item Shortage Report (stock bajo)

import unittest


class TestSetupStockDashboardAccess(unittest.TestCase):
	def test_stock_inventory_reports_include_item_shortage(self):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_stock_dashboard_access import (
			STOCK_INVENTORY_REPORTS,
		)

		self.assertIn("Item Shortage Report", STOCK_INVENTORY_REPORTS)

	def test_operative_roles_include_informatica(self):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_stock_dashboard_access import (
			OPERATIVE_ROLES,
		)

		self.assertIn("Informática", OPERATIVE_ROLES)
