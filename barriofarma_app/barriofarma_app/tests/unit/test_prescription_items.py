# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para agregar items de receta a ventas (Story 5.3)
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe import _
from frappe.exceptions import ValidationError
from barriofarma_app.barriofarma_app.utils.prescription_items import (
	get_prescription_items,
	add_prescription_items_to_invoice,
	validate_all_prescription_items_included
)


class TestPrescriptionItems(unittest.TestCase):
	"""Tests para agregar items de receta a ventas"""

	def setUp(self):
		self.prescription = MagicMock()
		self.prescription.items = []

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=False)
	@patch('frappe.get_doc')
	def test_get_prescription_items_receta_no_existe_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		"""Test: Obtener items de receta inexistente debe lanzar error"""
		import frappe
		# Configurar mock_throw para que lance excepción
		mock_throw.side_effect = frappe.ValidationError("Test error")
		
		# Debe lanzar error cuando la receta no existe
		with self.assertRaises(frappe.ValidationError):
			get_prescription_items("PRES-999")
		
		# Verificar que se llamó con el mensaje correcto
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("no existe", call_args.lower())

	@patch('frappe.get_doc')
	@patch('frappe.db.exists', return_value=True)
	def test_get_prescription_items_retorna_items(self, mock_db_exists, mock_get_doc):
		"""Test: Obtener items de receta válida retorna lista de items"""
		mock_prescription = MagicMock()
		mock_prescription_item = MagicMock()
		mock_prescription_item.item = "ITEM-001"
		mock_prescription_item.quantity = 10
		mock_prescription_item.get = lambda key, default=None: getattr(mock_prescription_item, key, default)
		mock_prescription.items = [mock_prescription_item]
		mock_prescription.get = lambda key, default=None: getattr(mock_prescription, key, default)
		
		mock_item = MagicMock()
		mock_item.item_name = "Medicamento Test"
		mock_item.stock_uom = "Unit"
		mock_item.standard_rate = 100.0
		
		def get_doc_side_effect(doctype, name):
			if doctype == "Prescription":
				return mock_prescription
			elif doctype == "Item":
				return mock_item
			raise Exception(f"Unexpected doctype: {doctype}")
		
		mock_get_doc.side_effect = get_doc_side_effect
		
		items = get_prescription_items("PRES-001")
		
		self.assertEqual(len(items), 1)
		self.assertEqual(items[0]["item_code"], "ITEM-001")
		self.assertEqual(items[0]["quantity"], 10)

	@patch('frappe.throw')
	@patch('frappe.db.exists')
	@patch('frappe.get_doc')
	def test_validate_all_prescription_items_included_items_faltantes_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		"""Test: Validar que todos los items de receta están incluidos - items faltantes lanzan error"""
		mock_db_exists.return_value = True
		
		invoice = MagicMock()
		invoice.get = lambda key, default=None: "PRES-001" if key == "custom_prescription" else getattr(invoice, key, default)
		invoice.custom_prescription = "PRES-001"
		
		# Item en la venta
		invoice_item = MagicMock()
		invoice_item.item_code = "ITEM-001"
		invoice_item.get = lambda key, default=None: getattr(invoice_item, key, default)
		invoice.items = [invoice_item]
		invoice.get = lambda key, default=None: invoice.items if key == "items" else (invoice.custom_prescription if key == "custom_prescription" else getattr(invoice, key, default))
		
		# Receta con 2 items
		mock_prescription = MagicMock()
		prescription_item1 = MagicMock()
		prescription_item1.item = "ITEM-001"
		prescription_item1.get = lambda key, default=None: getattr(prescription_item1, key, default)
		prescription_item2 = MagicMock()
		prescription_item2.item = "ITEM-002"  # Este falta en la venta
		prescription_item2.get = lambda key, default=None: getattr(prescription_item2, key, default)
		mock_prescription.items = [prescription_item1, prescription_item2]
		mock_prescription.get = lambda key, default=None: mock_prescription.items if key == "items" else getattr(mock_prescription, key, default)
		
		mock_get_doc.return_value = mock_prescription
		
		validate_all_prescription_items_included(invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("incluye medicamentos que no están", call_args.lower())

	@patch('frappe.throw')
	@patch('frappe.db.exists')
	@patch('frappe.get_doc')
	def test_validate_all_prescription_items_included_todos_incluidos_no_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		"""Test: Validar que todos los items de receta están incluidos - todos incluidos no lanzan error"""
		mock_db_exists.return_value = True
		
		invoice = MagicMock()
		invoice.get = lambda key, default=None: "PRES-001" if key == "custom_prescription" else getattr(invoice, key, default)
		invoice.custom_prescription = "PRES-001"
		
		# Items en la venta
		invoice_item1 = MagicMock()
		invoice_item1.item_code = "ITEM-001"
		invoice_item1.get = lambda key, default=None: getattr(invoice_item1, key, default)
		invoice_item2 = MagicMock()
		invoice_item2.item_code = "ITEM-002"
		invoice_item2.get = lambda key, default=None: getattr(invoice_item2, key, default)
		invoice.items = [invoice_item1, invoice_item2]
		invoice.get = lambda key, default=None: invoice.items if key == "items" else (invoice.custom_prescription if key == "custom_prescription" else getattr(invoice, key, default))
		
		# Receta con 2 items (mismos que en la venta)
		mock_prescription = MagicMock()
		prescription_item1 = MagicMock()
		prescription_item1.item = "ITEM-001"
		prescription_item1.get = lambda key, default=None: getattr(prescription_item1, key, default)
		prescription_item2 = MagicMock()
		prescription_item2.item = "ITEM-002"
		prescription_item2.get = lambda key, default=None: getattr(prescription_item2, key, default)
		mock_prescription.items = [prescription_item1, prescription_item2]
		mock_prescription.get = lambda key, default=None: mock_prescription.items if key == "items" else getattr(mock_prescription, key, default)
		
		mock_get_doc.return_value = mock_prescription
		
		validate_all_prescription_items_included(invoice)
		
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	def test_validate_all_prescription_items_included_sin_receta_no_valida(self, mock_throw):
		"""Test: Validar items de receta sin receta asociada no valida"""
		invoice = MagicMock()
		invoice.get = lambda key, default=None: None if key == "custom_prescription" else getattr(invoice, key, default)
		invoice.custom_prescription = None
		
		validate_all_prescription_items_included(invoice)
		
		mock_throw.assert_not_called()

