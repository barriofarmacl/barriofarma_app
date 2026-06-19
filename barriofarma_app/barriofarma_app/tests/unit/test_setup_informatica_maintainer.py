# -*- coding: utf-8 -*-
# Issue: barriofarma-number-cards-platform — Perfil Informática / Eduardo

import unittest
from unittest.mock import MagicMock, patch

MODULE = "barriofarma_app.barriofarma_app.utils.setup.setup_informatica_maintainer"


class TestSetupInformaticaMaintainer(unittest.TestCase):
	def test_maintainer_roles_include_system_manager(self):
		from barriofarma_app.barriofarma_app.utils.setup.setup_informatica_maintainer import (
			MAINTAINER_ROLES,
		)

		self.assertIn("System Manager", MAINTAINER_ROLES)
		self.assertIn("Dashboard Manager", MAINTAINER_ROLES)
		self.assertIn("Workspace Manager", MAINTAINER_ROLES)
		self.assertIn("Informática", MAINTAINER_ROLES)

	@patch(f"{MODULE}.frappe")
	def test_ensure_adds_missing_roles(self, mock_frappe):
		from barriofarma_app.barriofarma_app.utils.setup.setup_informatica_maintainer import (
			MAINTAINER_EMAIL,
			MAINTAINER_ROLES,
			ensure_informatica_maintainer_roles,
		)

		mock_frappe.db.exists.side_effect = lambda dt, name: True
		user = MagicMock()
		user.roles = [MagicMock(role="Informática")]
		mock_frappe.get_doc.return_value = user

		added = ensure_informatica_maintainer_roles()

		self.assertEqual(set(added), set(MAINTAINER_ROLES) - {"Informática"})
		user.save.assert_called_once()

	@patch(f"{MODULE}.frappe")
	def test_ensure_skips_when_user_missing(self, mock_frappe):
		from barriofarma_app.barriofarma_app.utils.setup.setup_informatica_maintainer import (
			ensure_informatica_maintainer_roles,
		)

		mock_frappe.db.exists.return_value = False
		self.assertEqual(ensure_informatica_maintainer_roles(), [])
		mock_frappe.get_doc.assert_not_called()


class TestPerfilInformaticaProfile(unittest.TestCase):
	def test_profile_roles(self):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_user_profiles import (
			USER_PROFILES,
		)

		profile = USER_PROFILES["Perfil Informática"]
		roles = set(profile["custom_roles"] + profile["standard_roles"])
		self.assertIn("Informática", roles)
		self.assertIn("System Manager", roles)
		self.assertIn("Dashboard Manager", roles)
		self.assertIn("Workspace Manager", roles)
