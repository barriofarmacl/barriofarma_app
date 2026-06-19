# -*- coding: utf-8 -*-
# Issue: barriofarma-number-cards-platform — acceso Informática a reportes Buying

import unittest
from unittest.mock import MagicMock, patch

MODULE = "barriofarma_app.barriofarma_app.utils.permissions.setup_buying_dashboard_access"


class TestSetupBuyingDashboardAccess(unittest.TestCase):
	def test_buying_dashboard_roles_include_informatica(self):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_buying_dashboard_access import (
			BUYING_DASHBOARD_ROLES,
		)

		self.assertIn("Farmacéutico", BUYING_DASHBOARD_ROLES)
		self.assertIn("Informática", BUYING_DASHBOARD_ROLES)
		self.assertNotIn("Auxiliar", BUYING_DASHBOARD_ROLES)

	@patch(f"{MODULE}._clear_report_role_cache")
	@patch(f"{MODULE}._ensure_report_roles")
	@patch(f"{MODULE}.frappe")
	def test_setup_adds_informatica_to_all_buying_reports(self, mock_frappe, mock_ensure, _mock_cache):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_buying_dashboard_access import (
			BUYING_DASHBOARD_REPORTS,
			BUYING_DASHBOARD_ROLES,
			setup_buying_dashboard_reports,
		)

		mock_ensure.return_value = ["Informática"]
		added = setup_buying_dashboard_reports()

		self.assertEqual(mock_ensure.call_count, len(BUYING_DASHBOARD_REPORTS))
		for call, report_name in zip(mock_ensure.call_args_list, BUYING_DASHBOARD_REPORTS):
			self.assertEqual(call.args, (report_name, BUYING_DASHBOARD_ROLES))
		self.assertEqual(len(added), len(BUYING_DASHBOARD_REPORTS))
		mock_frappe.db.commit.assert_called_once()
