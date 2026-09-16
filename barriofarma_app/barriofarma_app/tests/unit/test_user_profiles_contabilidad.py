# -*- coding: utf-8 -*-
# whiteboard #80 follow-up: Perfil Contabilidad MUST NOT expose Stock/Almacen.

import unittest

from barriofarma_app.barriofarma_app.utils.permissions.setup_user_profiles import (
	ADMIN_ERPNEXT_STANDARD_ROLES_CONTABILIDAD,
	USER_PROFILES,
)


class TestPerfilContabilidadModules(unittest.TestCase):
	def test_contabilidad_visible_modules_exclude_stock(self):
		profile = USER_PROFILES["Perfil Contabilidad"]
		self.assertNotIn("Stock", profile["visible_modules"])
		self.assertEqual(
			set(profile["visible_modules"]),
			{"Accounts", "Selling", "Buying"},
		)

	def test_contabilidad_hides_stock_desktop_icon(self):
		profile = USER_PROFILES["Perfil Contabilidad"]
		hidden = set(profile.get("hidden_desktop_icons") or [])
		self.assertIn("Stock", hidden)

	def test_contabilidad_standard_roles_exclude_stock_user(self):
		self.assertNotIn("Stock User", ADMIN_ERPNEXT_STANDARD_ROLES_CONTABILIDAD)
		self.assertNotIn(
			"Stock User",
			USER_PROFILES["Perfil Contabilidad"]["standard_roles"],
		)
