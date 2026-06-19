# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

MODULE = "barriofarma_app.barriofarma_app.utils.setup.setup_site_locale"


class TestLocaleResolution(unittest.TestCase):
	"""Resolucion: site_config.json/common -> env var -> fallback Chile."""

	@patch(f"{MODULE}.os")
	@patch(f"{MODULE}.frappe")
	def test_fallback_when_no_config(self, mock_frappe, mock_os):
		from barriofarma_app.barriofarma_app.utils.setup.setup_site_locale import (
			DEFAULT_LOCALE,
			get_barriofarma_locale,
		)

		mock_frappe.conf.get.return_value = None
		mock_os.environ.get.return_value = None

		self.assertEqual(get_barriofarma_locale(), DEFAULT_LOCALE)

	@patch(f"{MODULE}.os")
	@patch(f"{MODULE}.frappe")
	def test_site_config_overrides_fallback(self, mock_frappe, mock_os):
		from barriofarma_app.barriofarma_app.utils.setup.setup_site_locale import (
			get_barriofarma_locale,
		)

		conf = {
			"bf_time_zone": "America/Argentina/Buenos_Aires",
			"bf_country": "Argentina",
			"bf_language": "es",
			"bf_currency": "ARS",
		}
		mock_frappe.conf.get.side_effect = conf.get
		mock_os.environ.get.return_value = None

		locale = get_barriofarma_locale()
		self.assertEqual(locale["time_zone"], "America/Argentina/Buenos_Aires")
		self.assertEqual(locale["currency"], "ARS")

	@patch(f"{MODULE}.os")
	@patch(f"{MODULE}.frappe")
	def test_env_var_used_when_no_site_config(self, mock_frappe, mock_os):
		from barriofarma_app.barriofarma_app.utils.setup.setup_site_locale import (
			get_default_time_zone,
		)

		mock_frappe.conf.get.return_value = None
		mock_os.environ.get.side_effect = (
			lambda k: "America/Lima" if k == "BF_TIME_ZONE" else None
		)

		self.assertEqual(get_default_time_zone(), "America/Lima")


class TestEnsureSiteLocale(unittest.TestCase):
	@patch(f"{MODULE}.os")
	@patch(f"{MODULE}.frappe")
	def test_ensure_fixes_kolkata_to_resolved_tz(self, mock_frappe, mock_os):
		from barriofarma_app.barriofarma_app.utils.setup.setup_site_locale import (
			DEFAULT_LOCALE,
			ensure_barriofarma_site_locale,
		)

		mock_frappe.conf.get.return_value = None
		mock_os.environ.get.return_value = None

		def get_single(doctype, field):
			return {
				"time_zone": "Asia/Kolkata",
				"country": "Chile",
				"language": "es",
				"currency": "CLP",
			}.get(field)

		mock_frappe.db.get_single_value.side_effect = get_single

		with patch(
			"barriofarma_app.barriofarma_app.validations.user_timezone.ensure_all_users_americas_timezone",
			return_value=[],
		):
			changed = ensure_barriofarma_site_locale()

		mock_frappe.db.set_single_value.assert_any_call(
			"System Settings", "time_zone", DEFAULT_LOCALE["time_zone"]
		)
		self.assertTrue(any("time_zone" in c for c in changed))


if __name__ == "__main__":
	unittest.main()
