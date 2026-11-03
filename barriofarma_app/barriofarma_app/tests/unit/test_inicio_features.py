# Copyright (c) 2026, Barrio Farma and Contributors

import frappe
from frappe.tests.utils import FrappeTestCase

from barriofarma_app.barriofarma_app.utils.inicio.inicio_features import (
	catalogo_terreno_enabled,
)


class TestInicioFeatures(FrappeTestCase):
	def test_catalogo_enabled_by_default(self):
		frappe.conf.pop("inicio_catalogo_terreno_enabled", None)
		self.assertTrue(catalogo_terreno_enabled())

	def test_catalogo_disabled_via_site_config(self):
		frappe.conf.inicio_catalogo_terreno_enabled = 0
		self.addCleanup(lambda: frappe.conf.pop("inicio_catalogo_terreno_enabled", None))
		self.assertFalse(catalogo_terreno_enabled())
