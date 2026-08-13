# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Tests para setup POS Settings (campos receta en caja)."""

import unittest
from unittest.mock import MagicMock, patch

from barriofarma_app.barriofarma_app.utils.setup.setup_pos_receta_invoice_fields import (
	ensure_pos_receta_invoice_fields,
)


class _PosFieldRow:
	def __init__(self, fieldname):
		self.fieldname = fieldname


class TestSetupPosRecetaInvoiceFields(unittest.TestCase):
	@patch("barriofarma_app.barriofarma_app.utils.setup.setup_pos_receta_invoice_fields.frappe")
	def test_ensure_pos_receta_invoice_fields_idempotente(self, mock_frappe):
		settings = MagicMock()
		settings.invoice_fields = [_PosFieldRow("custom_patient")]
		mock_frappe.get_single.return_value = settings
		mock_meta = MagicMock()
		mock_meta.get_field.return_value = MagicMock(
			fieldname="custom_receta_medica",
			label="Receta Médica",
			fieldtype="Link",
			options="Receta Medica",
		)
		mock_frappe.get_meta.return_value = mock_meta

		added = ensure_pos_receta_invoice_fields()

		self.assertEqual(added, ["custom_receta_medica"])
		self.assertEqual(settings.invoice_type, "POS Invoice")
		settings.save.assert_called_once_with(ignore_permissions=True)
		mock_frappe.db.commit.assert_called_once()

	@patch("barriofarma_app.barriofarma_app.utils.setup.setup_pos_receta_invoice_fields.frappe")
	def test_ensure_pos_receta_invoice_fields_sin_cambios(self, mock_frappe):
		settings = MagicMock()
		settings.invoice_fields = [
			_PosFieldRow("custom_patient"),
			_PosFieldRow("custom_receta_medica"),
		]
		mock_frappe.get_single.return_value = settings

		added = ensure_pos_receta_invoice_fields()

		self.assertEqual(added, [])
		settings.save.assert_not_called()
