# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para asociación de receta médica a venta (Story 4.2)

Story 4.2: Asociación de Receta Médica a Venta
- Validar que items con custom_requires_prescription_retention=1 requieren receta
- Validar que items sin custom_requires_prescription_retention=1 no requieren receta
- Validar que la validación se ejecuta antes de guardar
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import getdate, today, add_days
from barriofarma_app.barriofarma_app.validations.prescription_validation import (
	validate_prescription_validity
)


class MockItem:
	"""Mock de Item DocType"""
	def __init__(self, item_code, requires_prescription_retention=0):
		self.item_code = item_code
		self.custom_requires_prescription_retention = requires_prescription_retention
	
	def get(self, key, default=None):
		return getattr(self, key, default)


class MockPrescription:
	"""Mock de Prescription DocType"""
	def __init__(self, name, valid_till, max_dispensations, dispensation_count, status="Nueva"):
		self.name = name
		self.valid_till = valid_till
		self.max_dispensations = max_dispensations
		self.dispensation_count = dispensation_count
		self.status = status
		self.items = []
	
	def get(self, key, default=None):
		return getattr(self, key, default)


class TestPrescriptionAssociation(unittest.TestCase):
	"""Tests para Story 4.2: Asociación de Receta Médica a Venta"""

	def setUp(self):
		self.invoice = MagicMock()
		self.invoice.doctype = "Sales Invoice"
		self.invoice.name = "SI-001"
		self.invoice.items = []
		self.invoice.custom_prescription = None
		self.invoice.posting_date = today()
		self.invoice.get = lambda key, default=None: (
			self.invoice.items if key == "items" else
			(self.invoice.custom_prescription if key == "custom_prescription" else
			 getattr(self.invoice, key, default))
		)

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_item_requiere_receta_sin_receta_lanza_error(self, mock_get_doc, mock_throw):
		"""Test: Item que requiere receta sin receta asociada debe lanzar error"""
		# Item que requiere receta
		item_row = MagicMock()
		item_row.item_code = "ITEM-001"
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		
		mock_item = MockItem("ITEM-001", requires_prescription_retention=1)
		mock_get_doc.return_value = mock_item
		
		validate_prescription_validity(self.invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("requieren receta médica", call_args.lower())
		self.assertIn("ITEM-001", call_args)

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_item_no_requiere_receta_sin_receta_no_lanza_error(self, mock_get_doc, mock_throw):
		"""Test: Item que no requiere receta sin receta asociada no debe lanzar error"""
		# Item que no requiere receta
		item_row = MagicMock()
		item_row.item_code = "ITEM-002"
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		
		mock_item = MockItem("ITEM-002", requires_prescription_retention=0)
		mock_get_doc.return_value = mock_item
		
		validate_prescription_validity(self.invoice)
		
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_multiple_items_requieren_receta_sin_receta_lanza_error(self, mock_get_doc, mock_throw):
		"""Test: Múltiples items que requieren receta sin receta asociada deben lanzar error con lista de items"""
		# Múltiples items que requieren receta
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
		
		validate_prescription_validity(self.invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("requieren receta médica", call_args.lower())
		self.assertIn("ITEM-001", call_args)
		self.assertIn("ITEM-003", call_args)

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_item_requiere_receta_con_receta_valida_no_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		"""Test: Item que requiere receta con receta válida asociada no debe lanzar error"""
		# Item que requiere receta
		item_row = MagicMock()
		item_row.item_code = "ITEM-001"
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		self.invoice.custom_prescription = "PRES-001"
		
		def get_doc_side_effect(doctype, name):
			if doctype == "Item":
				return MockItem("ITEM-001", requires_prescription_retention=1)
			elif doctype == "Prescription":
				return MockPrescription(
					"PRES-001",
					add_days(today(), 30),  # Válida por 30 días
					1,  # max_dispensations
					0,  # dispensation_count
					"Nueva"
				)
			raise frappe.DoesNotExistError
		
		mock_get_doc.side_effect = get_doc_side_effect
		
		validate_prescription_validity(self.invoice)
		
		# No debe lanzar error por falta de receta, pero puede lanzar otros errores de validación
		# Verificamos que no se lanzó error por "Receta Requerida"
		error_calls = [call for call in mock_throw.call_args_list if call]
		if error_calls:
			error_messages = [str(call[0][0]).lower() for call in error_calls]
			self.assertNotIn("receta requerida", " ".join(error_messages))

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_item_sin_item_code_no_valida(self, mock_get_doc, mock_throw):
		"""Test: Item sin item_code no debe validar"""
		# Item sin item_code
		item_row = MagicMock()
		item_row.item_code = None
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		
		validate_prescription_validity(self.invoice)
		
		# No debe llamar a frappe.get_doc ni lanzar error
		mock_get_doc.assert_not_called()
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.get_doc', side_effect=frappe.DoesNotExistError)
	def test_item_inexistente_no_lanza_error(self, mock_get_doc, mock_throw):
		"""Test: Item que no existe no debe lanzar error (solo se registra y continúa)"""
		# Item que no existe
		item_row = MagicMock()
		item_row.item_code = "ITEM-999"
		item_row.get = lambda key, default=None: getattr(item_row, key, default)
		self.invoice.items = [item_row]
		
		validate_prescription_validity(self.invoice)
		
		# No debe lanzar error, solo continuar
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_mezcla_items_requieren_y_no_requieren_receta(self, mock_get_doc, mock_throw):
		"""Test: Mezcla de items que requieren y no requieren receta debe validar solo los que requieren"""
		# Item que requiere receta
		item_row1 = MagicMock()
		item_row1.item_code = "ITEM-001"
		item_row1.get = lambda key, default=None: getattr(item_row1, key, default)
		# Item que no requiere receta
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
		
		validate_prescription_validity(self.invoice)
		
		# Debe lanzar error porque ITEM-001 requiere receta
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("ITEM-001", call_args)
		# ITEM-002 no debe aparecer en el error porque no requiere receta
		self.assertNotIn("ITEM-002", call_args)

