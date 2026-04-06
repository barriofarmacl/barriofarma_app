# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para validacion de vigencia de Receta Medica (Story 5.2)
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import getdate, today, add_days
from barriofarma_app.barriofarma_app.validations.receta_medica_validation import (
	validate_receta_medica_validity,
	update_receta_medica_dispensation
)


class TestRecetaMedicaValidation(unittest.TestCase):
	"""Tests para validacion de vigencia de receta"""

	def setUp(self):
		self.invoice = MagicMock()
		self.invoice.items = []
		self.invoice.custom_receta_medica = None
		self.invoice.posting_date = today()
		self.invoice.name = "SINV-001"
		self.invoice.doctype = "Sales Invoice"

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_receta_vencida_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		self.invoice.custom_receta_medica = "RX-001"
		mock_receta = MagicMock()
		mock_receta.valid_till = add_days(today(), -10)
		mock_receta.max_dispensations = 1
		mock_receta.dispensation_count = 0
		mock_receta.status = "Nueva"
		mock_receta.get = lambda key, default=None: getattr(mock_receta, key, default)
		mock_get_doc.return_value = mock_receta
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_called_once()
		self.assertIn("vencida", mock_throw.call_args[0][0].lower())

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_receta_valida_no_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		self.invoice.custom_receta_medica = "RX-001"
		mock_receta = MagicMock()
		mock_receta.valid_till = add_days(today(), 30)
		mock_receta.max_dispensations = 1
		mock_receta.dispensation_count = 0
		mock_receta.status = "Nueva"
		mock_receta.get = lambda key, default=None: getattr(mock_receta, key, default)
		mock_get_doc.return_value = mock_receta
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_receta_excede_max_dispensations_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		self.invoice.custom_receta_medica = "RX-001"
		mock_receta = MagicMock()
		mock_receta.valid_till = add_days(today(), 30)
		mock_receta.max_dispensations = 1
		mock_receta.dispensation_count = 1
		mock_receta.status = "Nueva"
		mock_receta.get = lambda key, default=None: getattr(mock_receta, key, default)
		mock_get_doc.return_value = mock_receta
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_called_once()

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_receta_estado_vencida_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		self.invoice.custom_receta_medica = "RX-001"
		mock_receta = MagicMock()
		mock_receta.valid_till = add_days(today(), 30)
		mock_receta.max_dispensations = 1
		mock_receta.dispensation_count = 0
		mock_receta.status = "Vencida"
		mock_receta.get = lambda key, default=None: getattr(mock_receta, key, default)
		mock_get_doc.return_value = mock_receta
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_called_once()

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=False)
	def test_receta_no_existe_lanza_error(self, mock_db_exists, mock_throw):
		mock_throw.side_effect = frappe.ValidationError("Test error")
		self.invoice.custom_receta_medica = "RX-999"
		with self.assertRaises(frappe.ValidationError):
			validate_receta_medica_validity(self.invoice)
		mock_throw.assert_called_once()
		self.assertIn("no existe", mock_throw.call_args[0][0].lower())

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_item_requiere_receta_sin_receta_lanza_error(self, mock_get_doc, mock_throw):
		item = MagicMock()
		item.item_code = "ITEM-001"
		self.invoice.items = [item]
		self.invoice.get = lambda key, default=None: None if key == "custom_receta_medica" else getattr(self.invoice, key, default)
		self.invoice.custom_receta_medica = None
		mock_item = MagicMock()
		mock_item.custom_requires_prescription_retention = 1
		mock_item.get = lambda key, default=None: getattr(mock_item, key, default)
		def get_doc_side_effect(doctype, name):
			if doctype == "Item":
				return mock_item
			raise Exception(f"Unexpected doctype: {doctype}")
		mock_get_doc.side_effect = get_doc_side_effect
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_called_once()
		self.assertIn("requieren receta", mock_throw.call_args[0][0].lower())

	@patch('frappe.log_error')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	@patch('frappe.session')
	@patch('frappe.db.commit')
	def test_update_receta_medica_dispensation_incrementa_count(self, mock_commit, mock_session, mock_get_doc, mock_db_exists, mock_log_error):
		mock_session.user = 'test_user'
		self.invoice.custom_receta_medica = "RX-001"
		mock_receta = MagicMock()
		mock_receta.dispensation_count = 0
		mock_receta.max_dispensations = 1
		mock_receta.status = "Nueva"
		mock_receta.related_sales_invoices = []
		mock_receta.get = lambda key, default=None: getattr(mock_receta, key, default)
		mock_receta.append = MagicMock()
		mock_receta.save = MagicMock()
		mock_receta.update_status = MagicMock()
		mock_get_doc.return_value = mock_receta
		update_receta_medica_dispensation(self.invoice)
		self.assertEqual(mock_receta.dispensation_count, 1)
		self.assertGreaterEqual(mock_receta.save.call_count, 1)
		mock_commit.assert_called()

	@patch('frappe.log_error')
	@patch('frappe.db.exists', return_value=False)
	@patch('frappe.db.rollback')
	def test_update_receta_medica_dispensation_receta_no_existe_log_error(self, mock_rollback, mock_db_exists, mock_log_error):
		self.invoice.custom_receta_medica = "RX-999"
		update_receta_medica_dispensation(self.invoice)
		mock_log_error.assert_called_once()
