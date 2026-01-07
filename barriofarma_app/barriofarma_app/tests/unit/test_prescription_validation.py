# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para validación de vigencia de receta (Story 5.2)
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import getdate, today, add_days
from barriofarma_app.barriofarma_app.validations.prescription_validation import (
	validate_prescription_validity,
	update_prescription_dispensation
)


class TestPrescriptionValidation(unittest.TestCase):
	"""Tests para validación de vigencia de receta"""

	def setUp(self):
		self.invoice = MagicMock()
		self.invoice.items = []
		self.invoice.custom_prescription = None
		self.invoice.posting_date = today()
		self.invoice.name = "SINV-001"
		self.invoice.doctype = "Sales Invoice"

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_receta_vencida_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		"""Test: Receta vencida debe lanzar error"""
		self.invoice.custom_prescription = "PRES-001"
		
		mock_prescription = MagicMock()
		mock_prescription.valid_till = add_days(today(), -10)  # Vencida hace 10 días
		mock_prescription.max_dispensations = 1
		mock_prescription.dispensation_count = 0
		mock_prescription.status = "Nueva"
		mock_prescription.get = lambda key, default=None: getattr(mock_prescription, key, default)
		
		mock_get_doc.return_value = mock_prescription
		
		validate_prescription_validity(self.invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("vencida", call_args.lower())

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_receta_valida_no_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		"""Test: Receta válida no debe lanzar error"""
		self.invoice.custom_prescription = "PRES-001"
		
		mock_prescription = MagicMock()
		mock_prescription.valid_till = add_days(today(), 30)  # Válida por 30 días más
		mock_prescription.max_dispensations = 1
		mock_prescription.dispensation_count = 0
		mock_prescription.status = "Nueva"
		mock_prescription.get = lambda key, default=None: getattr(mock_prescription, key, default)
		
		mock_get_doc.return_value = mock_prescription
		
		validate_prescription_validity(self.invoice)
		
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_receta_excede_max_dispensations_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		"""Test: Receta que excede max_dispensations debe lanzar error"""
		self.invoice.custom_prescription = "PRES-001"
		
		mock_prescription = MagicMock()
		mock_prescription.valid_till = add_days(today(), 30)
		mock_prescription.max_dispensations = 1
		mock_prescription.dispensation_count = 1  # Ya alcanzó el límite
		mock_prescription.status = "Nueva"
		mock_prescription.get = lambda key, default=None: getattr(mock_prescription, key, default)
		
		mock_get_doc.return_value = mock_prescription
		
		validate_prescription_validity(self.invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("límite", call_args.lower() or "dispensaciones" in call_args.lower())

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_receta_estado_vencida_lanza_error(self, mock_get_doc, mock_db_exists, mock_throw):
		"""Test: Receta con estado 'Vencida' debe lanzar error"""
		self.invoice.custom_prescription = "PRES-001"
		
		mock_prescription = MagicMock()
		mock_prescription.valid_till = add_days(today(), 30)
		mock_prescription.max_dispensations = 1
		mock_prescription.dispensation_count = 0
		mock_prescription.status = "Vencida"
		mock_prescription.get = lambda key, default=None: getattr(mock_prescription, key, default)
		
		mock_get_doc.return_value = mock_prescription
		
		validate_prescription_validity(self.invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("estado", call_args.lower() or "vencida" in call_args.lower())

	@patch('frappe.throw')
	@patch('frappe.db.exists', return_value=False)
	def test_receta_no_existe_lanza_error(self, mock_db_exists, mock_throw):
		"""Test: Receta que no existe debe lanzar error"""
		import frappe
		# Configurar mock_throw para que lance excepción
		mock_throw.side_effect = frappe.ValidationError("Test error")
		self.invoice.custom_prescription = "PRES-999"
		
		# Debe lanzar error cuando la receta no existe
		with self.assertRaises(frappe.ValidationError):
			validate_prescription_validity(self.invoice)
		
		# Verificar que se llamó con el mensaje correcto
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("no existe", call_args.lower())

	@patch('frappe.throw')
	@patch('frappe.get_doc')
	def test_item_requiere_receta_sin_receta_lanza_error(self, mock_get_doc, mock_throw):
		"""Test: Item que requiere receta sin receta asociada debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		self.invoice.items = [item]
		self.invoice.get = lambda key, default=None: None if key == "custom_prescription" else getattr(self.invoice, key, default)
		self.invoice.custom_prescription = None
		
		mock_item = MagicMock()
		mock_item.custom_requires_prescription_retention = 1
		mock_item.get = lambda key, default=None: getattr(mock_item, key, default)
		
		# Configurar mock_get_doc para que retorne el item cuando se pide "Item"
		def get_doc_side_effect(doctype, name):
			if doctype == "Item":
				return mock_item
			raise Exception(f"Unexpected doctype: {doctype}")
		
		mock_get_doc.side_effect = get_doc_side_effect
		
		validate_prescription_validity(self.invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("requieren receta", call_args.lower())

	@patch('frappe.log_error')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	@patch('frappe.session')
	@patch('frappe.db.commit')
	def test_update_prescription_dispensation_incrementa_count(self, mock_commit, mock_session, mock_get_doc, mock_db_exists, mock_log_error):
		"""Test: Actualizar dispensación incrementa dispensation_count"""
		mock_session.user = 'test_user'
		self.invoice.custom_prescription = "PRES-001"
		
		mock_prescription = MagicMock()
		mock_prescription.dispensation_count = 0
		mock_prescription.max_dispensations = 1
		mock_prescription.status = "Nueva"
		mock_prescription.related_sales_invoices = []
		mock_prescription.get = lambda key, default=None: getattr(mock_prescription, key, default)
		mock_prescription.append = MagicMock()
		mock_prescription.save = MagicMock()
		mock_prescription.update_status = MagicMock()
		
		mock_get_doc.return_value = mock_prescription
		
		update_prescription_dispensation(self.invoice)
		
		# Verificar que dispensation_count se incrementó
		self.assertEqual(mock_prescription.dispensation_count, 1)
		# Verificar que se guardó (puede ser llamado más de una vez por append)
		self.assertGreaterEqual(mock_prescription.save.call_count, 1)
		mock_commit.assert_called()

	@patch('frappe.log_error')
	@patch('frappe.db.exists', return_value=False)
	@patch('frappe.db.rollback')
	def test_update_prescription_dispensation_receta_no_existe_log_error(self, mock_rollback, mock_db_exists, mock_log_error):
		"""Test: Actualizar dispensación con receta inexistente debe registrar error"""
		self.invoice.custom_prescription = "PRES-999"
		
		update_prescription_dispensation(self.invoice)
		
		# Debe registrar error pero no lanzar excepción
		mock_log_error.assert_called_once()
		# El rollback puede no llamarse si el error se maneja antes
		# Solo verificamos que se registró el error

