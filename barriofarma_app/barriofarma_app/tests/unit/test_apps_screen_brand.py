# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""El tile de Apps del Desk muestra BF / BarrioFarma sin tocar erpnext/hooks.py."""

import unittest

from barriofarma_app.barriofarma_app.utils.desk.apps_screen_brand import (
	APPS_SCREEN_LOGO,
	APPS_SCREEN_TITLE,
	apply_apps_screen_brand,
	apply_public_brand,
)


class TestAppsScreenBrand(unittest.TestCase):
	def test_erpnext_tile_uses_barriofarma_mark(self):
		bootinfo = {
			"app_data": [
				{
					"app_name": "erpnext",
					"app_title": "ERPNext",
					"app_logo_url": "/assets/erpnext/images/erpnext-logo.svg",
				},
				{
					"app_name": "frappe",
					"app_title": "Framework",
					"app_logo_url": "/assets/frappe/images/frappe-framework-logo.svg",
				},
			]
		}

		apply_apps_screen_brand(bootinfo)

		erpnext, framework = bootinfo["app_data"]
		self.assertEqual(erpnext["app_title"], APPS_SCREEN_TITLE)
		self.assertEqual(erpnext["app_logo_url"], APPS_SCREEN_LOGO)
		self.assertEqual(framework["app_title"], "Framework")
		self.assertTrue(framework["app_logo_url"].endswith("frappe-framework-logo.svg"))

	def test_missing_app_data_is_a_no_op(self):
		bootinfo = {}
		apply_apps_screen_brand(bootinfo)
		self.assertEqual(bootinfo, {})

	def test_login_usa_el_isotipo_barriofarma(self):
		brand = apply_public_brand({})
		self.assertEqual(brand["logo"], APPS_SCREEN_LOGO)
		self.assertEqual(brand["favicon"], APPS_SCREEN_LOGO)
		self.assertEqual(brand["splash_image"], APPS_SCREEN_LOGO)

	def test_splash_y_favicon_usan_el_isotipo_barriofarma(self):
		import frappe

		context = frappe.get_hooks("website_context")
		for key in ("splash_image", "favicon"):
			values = context.get(key) or []
			self.assertEqual(values[-1], APPS_SCREEN_LOGO)
