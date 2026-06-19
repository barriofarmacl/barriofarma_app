# -*- coding: utf-8 -*-

import unittest

from barriofarma_app.barriofarma_app.validations.user_timezone import (
	is_americas_timezone,
)


class TestUserAmericasTimezone(unittest.TestCase):
	def test_americas_timezone_allowed(self):
		self.assertTrue(is_americas_timezone("America/Santiago"))
		self.assertTrue(is_americas_timezone("America/New_York"))

	def test_non_americas_timezone_rejected(self):
		self.assertFalse(is_americas_timezone("Asia/Kolkata"))
		self.assertFalse(is_americas_timezone("Europe/Madrid"))
		self.assertFalse(is_americas_timezone(""))

	def test_validate_raises_for_kolkata(self):
		from frappe.exceptions import ValidationError

		import frappe

		from barriofarma_app.barriofarma_app.validations.user_timezone import (
			validate_user_americas_timezone,
		)

		doc = frappe._dict(name="test.user@barriofarma.cl", time_zone="Asia/Kolkata")
		with self.assertRaises(ValidationError):
			validate_user_americas_timezone(doc)

	def test_default_on_empty(self):
		from barriofarma_app.barriofarma_app.validations.user_timezone import (
			apply_default_user_timezone,
		)
		from barriofarma_app.barriofarma_app.utils.setup.setup_site_locale import (
			BARRIOFARMA_TIME_ZONE,
		)

		doc = type("Doc", (), {"name": "daniela.araya@barriofarma.cl", "time_zone": None})()
		apply_default_user_timezone(doc)
		self.assertEqual(doc.time_zone, BARRIOFARMA_TIME_ZONE)
