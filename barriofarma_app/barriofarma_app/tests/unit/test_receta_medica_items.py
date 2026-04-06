# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para items de Receta Medica en ventas (Story 5.3)
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe import _
from frappe.exceptions import ValidationError
from barriofarma_app.barriofarma_app.utils.domain.receta_medica_items import (
	get_receta_medica_items,
	add_receta_medica_items_to_invoice,
	validate_all_receta_medica_items_included
)


class TestRecetaMedicaItems(unittest.TestCase):
	"""Tests para items de receta en ventas"""

	def setUp(self):
		self.receta = MagicMock()
		self.receta.items = []

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=False)
	def test_get_receta_medica_items_receta_no_existe_lanza_error(self, mock_db_exists, mock_throw):
		mock_throw.side_effect = frappe.ValidationError("Test error")
		with self.assertRaises(frappe.ValidationError):
			get_receta_medica_items("RX-999")
		mock_throw.assert_called_once()
		self.assertIn("no existe", mock_throw.call_args[0][0].lower())

	@patch('frappe.get_doc')
	@patch('frappe.db.exists', return_value=True)
	def test_get_receta_medica_items_retorna_items(self, mock_db_exists, mock_get_doc):
		mock_receta = MagicMock()
		mock_receta_item = MagicMock()
		mock_receta_item.item = "ITEM-001"
		mock_receta_item.quantity = 10
		mock_receta_item.get = lambda key, default=None: getattr(mock_receta_item, key, default)
		mock_receta.items = [mock_receta_item]
		mock_receta.get = lambda key, default=None: getattr(mock_receta, key, default)
		mock_item = MagicMock()
		mock_item.item_name = "Medicamento Test"
		mock_item.stock_uom = "Unit"
		mock_item.standard_rate = 100.0
		def get_doc_side_effect(doctype, name):
			if doctype == "Receta Medica":
				return mock_receta
			elif doctype == "Item":
				return mock_item
			raise Exception(f"Unexpected doctype: {doctype}")
		mock_get_doc.side_effect = get_doc_side_effect
		items = get_receta_medica_items("RX-001")
		self.assertEqual(len(items), 1)
		self.assertEqual(items[0]["item_code"], "ITEM-001")
		self.assertEqual(items[0]["quantity"], 10)

	@patch('frappe.throw')
	@patch('frappe.db.exists')
	@patch('frappe.get_doc')
	def test_validate_all_receta_medica_items_included_items_faltantes_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		mock_db_exists.return_value = True
		invoice = MagicMock()
		invoice.custom_receta_medica = "RX-001"
		invoice_item = MagicMock()
		invoice_item.item_code = "ITEM-001"
		invoice_item.get = lambda key, default=None: getattr(invoice_item, key, default)
		invoice.items = [invoice_item]
		invoice.get = lambda key, default=None: invoice.items if key == "items" else (invoice.custom_receta_medica if key == "custom_receta_medica" else getattr(invoice, key, default))
		mock_receta = MagicMock()
		ri1 = MagicMock()
		ri1.item = "ITEM-001"
		ri1.get = lambda key, default=None: getattr(ri1, key, default)
		ri2 = MagicMock()
		ri2.item = "ITEM-002"
		ri2.get = lambda key, default=None: getattr(ri2, key, default)
		mock_receta.items = [ri1, ri2]
		mock_receta.get = lambda key, default=None: mock_receta.items if key == "items" else getattr(mock_receta, key, default)
		mock_get_doc.return_value = mock_receta
		validate_all_receta_medica_items_included(invoice)
		mock_throw.assert_called_once()
		self.assertIn("incluye medicamentos que no estan", mock_throw.call_args[0][0].lower())

	@patch('frappe.throw')
	@patch('frappe.db.exists')
	@patch('frappe.get_doc')
	def test_validate_all_receta_medica_items_included_todos_incluidos_no_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		mock_db_exists.return_value = True
		invoice = MagicMock()
		invoice.custom_receta_medica = "RX-001"
		invoice_item1 = MagicMock()
		invoice_item1.item_code = "ITEM-001"
		invoice_item1.get = lambda key, default=None: getattr(invoice_item1, key, default)
		invoice_item2 = MagicMock()
		invoice_item2.item_code = "ITEM-002"
		invoice_item2.get = lambda key, default=None: getattr(invoice_item2, key, default)
		invoice.items = [invoice_item1, invoice_item2]
		invoice.get = lambda key, default=None: invoice.items if key == "items" else (invoice.custom_receta_medica if key == "custom_receta_medica" else getattr(invoice, key, default))
		mock_receta = MagicMock()
		ri1 = MagicMock()
		ri1.item = "ITEM-001"
		ri1.get = lambda key, default=None: getattr(ri1, key, default)
		ri2 = MagicMock()
		ri2.item = "ITEM-002"
		ri2.get = lambda key, default=None: getattr(ri2, key, default)
		mock_receta.items = [ri1, ri2]
		mock_receta.get = lambda key, default=None: mock_receta.items if key == "items" else getattr(mock_receta, key, default)
		mock_get_doc.return_value = mock_receta
		validate_all_receta_medica_items_included(invoice)
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	def test_validate_all_receta_medica_items_included_sin_receta_no_valida(self, mock_throw):
		invoice = MagicMock()
		invoice.get = lambda key, default=None: None if key == "custom_receta_medica" else getattr(invoice, key, default)
		invoice.custom_receta_medica = None
		validate_all_receta_medica_items_included(invoice)
		mock_throw.assert_not_called()
