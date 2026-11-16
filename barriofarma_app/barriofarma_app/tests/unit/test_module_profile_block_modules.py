# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Module Profile guarda block_modules. No tiene child table roles."""

import unittest
from unittest.mock import MagicMock, patch

from barriofarma_app.barriofarma_app.utils.permissions.setup_user_profiles import (
	USER_PROFILES,
	create_or_update_module_profile,
	profile_module_sets,
)


class TestModuleProfileBlockModules(unittest.TestCase):
	def test_administrativo_blocks_modules_outside_the_profile(self):
		universe = {
			"Selling",
			"Buying",
			"Stock",
			"Accounts",
			"Desk",
			"Barriofarma App",
			"Assets",
			"CRM",
		}
		allowed, blocked = profile_module_sets(USER_PROFILES["Perfil Administrativo"], universe)

		self.assertIn("Accounts", allowed)
		self.assertIn("Stock", allowed)
		self.assertIn("Desk", allowed)
		self.assertIn("Assets", blocked)
		self.assertIn("CRM", blocked)
		self.assertNotIn("Accounts", blocked)

	@patch("barriofarma_app.barriofarma_app.utils.permissions.setup_user_profiles.frappe")
	def test_writer_appends_block_modules_not_roles(self, mock_frappe):
		doc = MagicMock()
		doc.name = "Module Profile - Perfil Administrativo"
		doc.get.return_value = []
		mock_frappe.db.exists.return_value = "Module Profile - Perfil Administrativo"
		mock_frappe.get_doc.return_value = doc

		create_or_update_module_profile(doc.name, ["Assets", "CRM"])

		appended = [call.args[0] for call in doc.append.call_args_list]
		self.assertEqual(appended, ["block_modules", "block_modules"])
		self.assertNotIn("roles", appended)
		doc.save.assert_called_once_with(ignore_permissions=True)
