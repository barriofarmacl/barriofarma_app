# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# Issue #68 — change permissions-fixtures-no-devmode
# Spec S2, S3, S9 — Custom DocPerm API without DocType.save on standard doctypes

import unittest
from unittest.mock import MagicMock, Mock, patch

MODULE = "barriofarma_app.barriofarma_app.utils.permissions.setup_permissions"


class TestSetupPermissionsCustomDocperm(unittest.TestCase):
	@patch(f"{MODULE}.frappe.db.commit")
	@patch(f"{MODULE}.frappe.get_doc")
	@patch(f"{MODULE}.frappe.db.get_value")
	@patch(f"{MODULE}.frappe.db.exists")
	@patch(f"{MODULE}.frappe.permissions.setup_custom_perms")
	def test_set_docperm_standard_doctype_calls_setup_custom_perms(
		self, mock_setup_custom_perms, mock_exists, mock_get_value, mock_get_doc, mock_commit
	):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import set_docperm

		mock_exists.return_value = True
		mock_get_value.side_effect = [1, 0, None]
		mock_cdp = MagicMock()
		mock_get_doc.return_value = mock_cdp

		result = set_docperm("Purchase Order", "Farmacéutico", ["R", "W", "C", "S"])

		self.assertTrue(result)
		mock_setup_custom_perms.assert_called_once_with("Purchase Order")
		for call in mock_get_doc.call_args_list:
			self.assertNotEqual(call.args[0], "DocType")

	@patch(f"{MODULE}.frappe.db.commit")
	@patch(f"{MODULE}.frappe.get_doc")
	@patch(f"{MODULE}.frappe.db.get_value")
	@patch(f"{MODULE}.frappe.db.exists")
	@patch(f"{MODULE}.frappe.permissions.setup_custom_perms")
	def test_set_docperm_standard_doctype_upserts_custom_docperm_row(
		self, mock_setup_custom_perms, mock_exists, mock_get_value, mock_get_doc, mock_commit
	):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import set_docperm

		mock_exists.return_value = True
		mock_get_value.side_effect = lambda dt, name, field=None, **kwargs: {
			("DocType", "Purchase Order", "custom"): 0,
			("DocType", "Purchase Order", "is_submittable"): 1,
		}.get((dt, name, field))

		mock_cdp = MagicMock()
		mock_get_doc.return_value = mock_cdp

		with patch(f"{MODULE}.frappe.db.get_value", side_effect=[
			0,  # custom
			1,  # is_submittable
			"CDP-001",  # existing Custom DocPerm name
		]):
			result = set_docperm("Purchase Order", "Farmacéutico", ["R", "W", "C", "S"])

		self.assertTrue(result)
		mock_cdp.save.assert_called_once_with(ignore_permissions=True)
		self.assertTrue(mock_cdp.read)
		self.assertTrue(mock_cdp.write)

	@patch(f"{MODULE}.frappe.db.commit")
	@patch(f"{MODULE}.frappe.delete_doc")
	@patch(f"{MODULE}.frappe.db.get_value")
	@patch(f"{MODULE}.frappe.db.exists")
	@patch(f"{MODULE}.frappe.permissions.setup_custom_perms")
	def test_set_docperm_empty_deletes_custom_row_only(
		self, mock_setup_custom_perms, mock_exists, mock_get_value, mock_delete_doc, mock_commit
	):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import set_docperm

		mock_exists.return_value = True
		mock_get_value.side_effect = [0, "CDP-001"]

		result = set_docperm("Purchase Order", "Auxiliar", [])

		self.assertTrue(result)
		mock_setup_custom_perms.assert_not_called()
		mock_delete_doc.assert_called_once_with(
			"Custom DocPerm", "CDP-001", ignore_permissions=True, force=True
		)

	@patch(f"{MODULE}.frappe.db.commit")
	@patch(f"{MODULE}.frappe.delete_doc")
	@patch(f"{MODULE}.frappe.db.get_value")
	@patch(f"{MODULE}.frappe.db.exists")
	def test_set_docperm_empty_idempotent_when_row_missing(
		self, mock_exists, mock_get_value, mock_delete_doc, mock_commit
	):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import set_docperm

		mock_exists.return_value = True
		mock_get_value.side_effect = [0, None, 0, None]

		self.assertTrue(set_docperm("Stock Entry", "Auxiliar", []))
		self.assertTrue(set_docperm("Stock Entry", "Auxiliar", []))
		mock_delete_doc.assert_not_called()

	@patch(f"{MODULE}.frappe.db.commit")
	@patch(f"{MODULE}.frappe.get_doc")
	@patch(f"{MODULE}.frappe.db.get_value")
	@patch(f"{MODULE}.frappe.db.exists")
	@patch(f"{MODULE}.frappe.permissions.setup_custom_perms")
	def test_set_docperm_idempotent_second_grant(
		self, mock_setup_custom_perms, mock_exists, mock_get_value, mock_get_doc, mock_commit
	):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import set_docperm

		mock_exists.return_value = True
		mock_cdp = MagicMock()
		mock_get_doc.return_value = mock_cdp

		def get_value_side_effect(doctype, filters=None, fieldname=None):
			if doctype == "DocType" and fieldname == "custom":
				return 0
			if doctype == "DocType" and fieldname == "is_submittable":
				return 0
			if doctype == "Custom DocPerm":
				return "CDP-001"
			return None

		mock_get_value.side_effect = get_value_side_effect

		perms = ["R", "W"]
		self.assertTrue(set_docperm("Item", "Bodeguero", perms))
		self.assertTrue(set_docperm("Item", "Bodeguero", perms))
		self.assertEqual(mock_setup_custom_perms.call_count, 2)
		self.assertEqual(mock_cdp.save.call_count, 2)

	@patch(f"{MODULE}.frappe.permissions.setup_custom_perms")
	@patch(f"{MODULE}.frappe.db.exists")
	def test_set_docperm_skips_when_doctype_or_role_missing(self, mock_exists, mock_setup_custom_perms):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import set_docperm

		mock_exists.return_value = False
		self.assertFalse(set_docperm("Missing DocType", "Farmacéutico", ["R"]))
		mock_setup_custom_perms.assert_not_called()

	@patch(f"{MODULE}.frappe.db.commit")
	@patch(f"{MODULE}.frappe.db.get_value")
	@patch(f"{MODULE}.frappe.db.exists")
	@patch(f"{MODULE}.frappe.permissions.setup_custom_perms")
	def test_custom_doctype_uses_legacy_doctype_save_path(
		self, mock_setup_custom_perms, mock_exists, mock_get_value, mock_commit
	):
		from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import set_docperm

		mock_exists.return_value = True
		mock_get_value.side_effect = lambda dt, name, field=None: {
			("DocType", "Custom Test Doc", "custom"): 1,
			("DocType", "Custom Test Doc", "is_submittable"): 0,
		}.get((dt, name, field))

		mock_doctype_doc = MagicMock()
		mock_doctype_doc.permissions = []
		mock_doctype_doc.is_submittable = 0

		with patch(f"{MODULE}.frappe.get_doc", return_value=mock_doctype_doc):
			result = set_docperm("Custom Test Doc", "Farmacéutico", ["R", "W"])

		self.assertTrue(result)
		mock_setup_custom_perms.assert_not_called()
		mock_doctype_doc.save.assert_called_once_with(ignore_permissions=True)
