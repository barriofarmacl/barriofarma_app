# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Regresión: sitio Barriofarma no debe cargar fixtures Company de ERPNext en tests."""

import unittest
from unittest.mock import MagicMock, patch

from barriofarma_app.barriofarma_app.utils.setup.test_site_company_guard import (
	PRODUCTION_COMPANIES,
	_should_skip_test_records,
	is_barriofarma_operational_site,
)


class TestErpnextCompanyGuard(unittest.TestCase):
	def test_production_companies_include_barriofarma(self):
		self.assertIn("Barriofarma", PRODUCTION_COMPANIES)

	@patch("barriofarma_app.barriofarma_app.utils.setup.test_site_company_guard.frappe")
	def test_operational_site_when_barriofarma_exists(self, mock_frappe):
		mock_frappe.db = MagicMock()
		mock_frappe.db.exists.return_value = True
		self.assertTrue(is_barriofarma_operational_site())
		mock_frappe.db.exists.assert_called_with("Company", "Barriofarma")

	@patch(
		"barriofarma_app.barriofarma_app.utils.setup.test_site_company_guard.is_barriofarma_operational_site",
		return_value=True,
	)
	def test_skip_company_test_records_on_operational_site(self, _mock_site):
		self.assertTrue(_should_skip_test_records("Company"))
		self.assertFalse(_should_skip_test_records("Item"))
