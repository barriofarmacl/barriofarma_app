# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para asociacion de Receta Medica a venta (Story 4.2)
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import getdate, today, add_days
from barriofarma_app.barriofarma_app.validations.receta_medica_validation import (
	validate_receta_medica_validity
)


class MockItem:
	def __init__(self, item_code, requires_prescription_retention=0):
		self.item_code = item_code
		self.custom_requires_prescription_retention = requires_prescription_retention

	def get(self, key, default=None):
		return getattr(self, key, default)


class MockRecetaMedica:
	def __init__(self, name, valid_till, max_dispensations, dispensation_count, status="Nueva"):
		self.name = name
		self.valid_till = valid_till
		self.max_dispensations = max_dispensations
		self.dispensation_count = dispensation_count
		self.status = status
		self.items = []

	def get(self, key, default=None):
		return getattr(self, key, default)


class TestRecetaMedicaAssociation(unittest.TestCase):
	"""Tests para Story 4.2: Asociacion de Receta Medica a Venta"""

	def setUp(self):
		self.invoice = MagicMock()
		self.invoice.doctype = "Sales Invoice"
		self.invoice.name = "SI-001"
		self.invoice.items = []
		self.invoice.custom_receta_medica = None
		self.invoice.posting_date = today()
		self.invoice.get = lambda key, default=None: (
			self.invoice.items if key == "items" else
			(self.invoice.custom_receta_medica if key == "custom_receta_medica" else
			 getattr(self.invoice, key, default))
		)

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_item_requiere_receta_sin_receta_lanza_error(self, mock_get_doc, mock_throw):
		item_row = MagicMock()
		item_row.item_code = "ITEM-001"
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		mock_item = MockItem("ITEM-001", requires_prescription_retention=1)
		mock_get_doc.return_value = mock_item
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("requieren receta medica", call_args.lower())
		self.assertIn("ITEM-001", call_args)

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_item_no_requiere_receta_sin_receta_no_lanza_error(self, mock_get_doc, mock_throw):
		item_row = MagicMock()
		item_row.item_code = "ITEM-002"
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		mock_item = MockItem("ITEM-002", requires_prescription_retention=0)
		mock_get_doc.return_value = mock_item
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_multiple_items_requieren_receta_sin_receta_lanza_error(self, mock_get_doc, mock_throw):
		item_row1 = MagicMock()
		item_row1.item_code = "ITEM-001"
		item_row1.get = lambda key, default=None: getattr(item_row1, key, default)
		item_row2 = MagicMock()
		item_row2.item_code = "ITEM-003"
		item_row2.get = lambda key, default=None: getattr(item_row2, key, default)
		self.invoice.items = [item_row1, item_row2]
		def get_doc_side_effect(doctype, name):
			if doctype == "Item":
				if name == "ITEM-001":
					return MockItem("ITEM-001", requires_prescription_retention=1)
				elif name == "ITEM-003":
					return MockItem("ITEM-003", requires_prescription_retention=1)
			raise frappe.DoesNotExistError
		mock_get_doc.side_effect = get_doc_side_effect
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("requieren receta medica", call_args.lower())
		self.assertIn("ITEM-001", call_args)
		self.assertIn("ITEM-003", call_args)

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_item_requiere_receta_con_receta_valida_no_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		item_row = MagicMock()
		item_row.item_code = "ITEM-001"
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		self.invoice.custom_receta_medica = "RX-001"
		def get_doc_side_effect(doctype, name):
			if doctype == "Item":
				return MockItem("ITEM-001", requires_prescription_retention=1)
			elif doctype == "Receta Medica":
				return MockRecetaMedica("RX-001", add_days(today(), 30), 1, 0, "Nueva")
			raise frappe.DoesNotExistError
		mock_get_doc.side_effect = get_doc_side_effect
		validate_receta_medica_validity(self.invoice)
		if mock_throw.call_args_list:
			error_messages = " ".join([str(c[0][0]).lower() for c in mock_throw.call_args_list])
			self.assertNotIn("receta requerida", error_messages)

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_item_sin_item_code_no_valida(self, mock_get_doc, mock_throw):
		item_row = MagicMock()
		item_row.item_code = None
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		validate_receta_medica_validity(self.invoice)
		mock_get_doc.assert_not_called()
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.get_doc', side_effect=frappe.DoesNotExistError)
	def test_item_inexistente_no_lanza_error(self, mock_get_doc, mock_throw):
		item_row = MagicMock()
		item_row.item_code = "ITEM-999"
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_mezcla_items_requieren_y_no_requieren_receta(self, mock_get_doc, mock_throw):
		item_row1 = MagicMock()
		item_row1.item_code = "ITEM-001"
		item_row1.get = lambda key, default=None: getattr(item_row1, key, default)
		item_row2 = MagicMock()
		item_row2.item_code = "ITEM-002"
		item_row2.get = lambda key, default=None: getattr(item_row2, key, default)
		self.invoice.items = [item_row1, item_row2]
		def get_doc_side_effect(doctype, name):
			if doctype == "Item":
				if name == "ITEM-001":
					return MockItem("ITEM-001", requires_prescription_retention=1)
				elif name == "ITEM-002":
					return MockItem("ITEM-002", requires_prescription_retention=0)
			raise frappe.DoesNotExistError
		mock_get_doc.side_effect = get_doc_side_effect
		validate_receta_medica_validity(self.invoice)
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("ITEM-001", call_args)
		self.assertNotIn("ITEM-002", call_args)
