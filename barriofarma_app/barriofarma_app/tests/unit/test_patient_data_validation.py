# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para validación de datos mínimos de cliente/paciente.

Story 4.3: Registro de Datos Mínimos de Cliente/Paciente
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe.exceptions import ValidationError
from barriofarma_app.barriofarma_app.validations.patient_data import validate_patient_data_required


class TestPatientDataValidation(unittest.TestCase):
	"""Tests para validación de datos de paciente"""
	
	def setUp(self):
		"""Configurar mocks para cada test"""
		self.invoice = MagicMock()
		self.invoice.name = "TEST-SI-001"
		self.invoice.items = []
		self.invoice.customer = "TEST-CUSTOMER"
	
	def test_sin_items_no_valida(self):
		"""Test: Si no hay items, no debe validar"""
		self.invoice.items = []
		
		with patch('frappe.throw') as mock_throw:
			validate_patient_data_required(self.invoice)
			mock_throw.assert_not_called()
	
	def test_item_sin_control_level_no_requiere_datos(self):
		"""Test: Item sin control level no requiere datos de paciente"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.item_name = "Item Normal"
		self.invoice.items = [item]
		
		mock_item_doc = MagicMock()
		mock_item_doc.get.side_effect = lambda x, default=None: {
			"custom_control_level": None,
			"custom_requires_prescription_retention": 0
		}.get(x, default)
		
		with patch('frappe.get_doc', return_value=mock_item_doc):
			with patch('frappe.throw') as mock_throw:
				validate_patient_data_required(self.invoice)
				mock_throw.assert_not_called()
	
	def test_item_psicotropico_requiere_datos(self):
		"""Test: Item Psicotrópico requiere datos de paciente"""
		item = MagicMock()
		item.item_code = "ITEM-PSICO"
		item.item_name = "Medicamento Psicotrópico"
		self.invoice.items = [item]
		
		mock_item_doc = MagicMock()
		mock_item_doc.get.side_effect = lambda x, default=None: {
			"custom_control_level": "Psicotrópico",
			"custom_requires_prescription_retention": 0
		}.get(x, default)
		
		mock_customer = MagicMock()
		mock_customer.customer_name = "Cliente Test"
		mock_customer.get.side_effect = lambda x, default=None: {
			"customer_name": mock_customer.customer_name,
			"custom_rut": None
		}.get(x, default)
		# Asegurar que customer_name.strip() funcione
		
		with patch('frappe.get_doc') as mock_get_doc:
			mock_get_doc.side_effect = [mock_item_doc, mock_customer]
			with patch('frappe.throw') as mock_throw:
				validate_patient_data_required(self.invoice)
				# No debe lanzar error si tiene nombre (RUT es opcional)
				mock_throw.assert_not_called()
	
	def test_item_psicotropico_sin_cliente_lanza_error(self):
		"""Test: Item Psicotrópico sin cliente debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-PSICO"
		item.item_name = "Medicamento Psicotrópico"
		self.invoice.items = [item]
		self.invoice.customer = None  # Sin cliente
		
		mock_item_doc = MagicMock()
		mock_item_doc.get.side_effect = lambda x, default=None: {
			"custom_control_level": "Psicotrópico",
			"custom_requires_prescription_retention": 0
		}.get(x, default)
		
		with patch('frappe.get_doc', return_value=mock_item_doc):
			with patch('frappe.throw') as mock_throw:
				validate_patient_data_required(self.invoice)
				mock_throw.assert_called_once()
				call_args = mock_throw.call_args[0][0]
				self.assertIn("cliente", call_args.lower())
	
	def test_cliente_sin_nombre_lanza_error(self):
		"""Test: Cliente sin nombre debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-PSICO"
		item.item_name = "Medicamento Psicotrópico"
		self.invoice.items = [item]
		
		mock_item_doc = MagicMock()
		mock_item_doc.get.side_effect = lambda x, default=None: {
			"custom_control_level": "Psicotrópico",
			"custom_requires_prescription_retention": 0
		}.get(x, default)
		
		mock_customer = MagicMock()
		mock_customer.customer_name = ""  # Sin nombre
		mock_customer.get.side_effect = lambda x: {
			"custom_rut": None
		}.get(x)
		
		with patch('frappe.get_doc') as mock_get_doc:
			mock_get_doc.side_effect = [mock_item_doc, mock_customer]
			with patch('frappe.throw') as mock_throw:
				validate_patient_data_required(self.invoice)
				mock_throw.assert_called_once()
				call_args = mock_throw.call_args[0][0]
				self.assertIn("nombre", call_args.lower())
	
	def test_cliente_con_rut_invalido_lanza_error(self):
		"""Test: Cliente con RUT inválido debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-PSICO"
		item.item_name = "Medicamento Psicotrópico"
		self.invoice.items = [item]
		
		mock_item_doc = MagicMock()
		mock_item_doc.get.side_effect = lambda x, default=None: {
			"custom_control_level": "Psicotrópico",
			"custom_requires_prescription_retention": 0
		}.get(x, default)
		
		mock_customer = MagicMock()
		mock_customer.customer_name = "Cliente Test"
		mock_customer.get.side_effect = lambda x, default=None: {
			"customer_name": mock_customer.customer_name,
			"custom_rut": "RUT-INVALIDO"
		}.get(x, default)
		# Asegurar que customer_name.strip() funcione
		
		with patch('frappe.get_doc') as mock_get_doc:
			mock_get_doc.side_effect = [mock_item_doc, mock_customer]
			with patch('barriofarma_app.barriofarma_app.validations.patient_data.validate_rut_format', return_value=(False, None, "Formato inválido")):
				with patch('frappe.throw') as mock_throw:
					validate_patient_data_required(self.invoice)
					# Debe lanzar error por RUT inválido (después de validar nombre)
					mock_throw.assert_called()
					# Verificar que el último error es por RUT
					last_call = mock_throw.call_args_list[-1]
					call_args = last_call[0][0]
					self.assertIn("RUT", call_args)
	
	def test_cliente_con_rut_valido_no_lanza_error(self):
		"""Test: Cliente con RUT válido no debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-PSICO"
		item.item_name = "Medicamento Psicotrópico"
		self.invoice.items = [item]
		
		mock_item_doc = MagicMock()
		mock_item_doc.get.side_effect = lambda x, default=None: {
			"custom_control_level": "Psicotrópico",
			"custom_requires_prescription_retention": 0
		}.get(x, default)
		
		mock_customer = MagicMock()
		mock_customer.customer_name = "Cliente Test"
		mock_customer.get.side_effect = lambda x, default=None: {
			"customer_name": mock_customer.customer_name,
			"custom_rut": "12.345.678-9"
		}.get(x, default)
		# Asegurar que customer_name.strip() funcione
		
		with patch('frappe.get_doc') as mock_get_doc:
			mock_get_doc.side_effect = [mock_item_doc, mock_customer]
			with patch('barriofarma_app.barriofarma_app.validations.patient_data.validate_rut_format', return_value=(True, "123456789", None)):
				with patch('frappe.throw') as mock_throw:
					validate_patient_data_required(self.invoice)
					mock_throw.assert_not_called()
	
	def test_item_requiere_receta_requiere_datos(self):
		"""Test: Item que requiere receta requiere datos de paciente"""
		item = MagicMock()
		item.item_code = "ITEM-RECETA"
		item.item_name = "Medicamento con Receta"
		self.invoice.items = [item]
		
		mock_item_doc = MagicMock()
		mock_item_doc.get.side_effect = lambda x, default=None: {
			"custom_control_level": None,
			"custom_requires_prescription_retention": 1
		}.get(x, default)
		
		mock_customer = MagicMock()
		mock_customer.customer_name = "Cliente Test"
		mock_customer.get.side_effect = lambda x, default=None: {
			"customer_name": mock_customer.customer_name,
			"custom_rut": None
		}.get(x, default)
		# Asegurar que customer_name.strip() funcione
		
		with patch('frappe.get_doc') as mock_get_doc:
			mock_get_doc.side_effect = [mock_item_doc, mock_customer]
			with patch('frappe.throw') as mock_throw:
				validate_patient_data_required(self.invoice)
				# No debe lanzar error si tiene nombre
				mock_throw.assert_not_called()
	
	def test_multiple_items_requieren_datos(self):
		"""Test: Múltiples items que requieren datos deben validar"""
		item1 = MagicMock()
		item1.item_code = "ITEM-PSICO"
		item1.item_name = "Medicamento Psicotrópico"
		
		item2 = MagicMock()
		item2.item_code = "ITEM-ESTUP"
		item2.item_name = "Medicamento Estupefaciente"
		
		self.invoice.items = [item1, item2]
		
		mock_item_doc1 = MagicMock()
		mock_item_doc1.get.side_effect = lambda x, default=None: {
			"custom_control_level": "Psicotrópico",
			"custom_requires_prescription_retention": 0
		}.get(x, default)
		
		mock_item_doc2 = MagicMock()
		mock_item_doc2.get.side_effect = lambda x, default=None: {
			"custom_control_level": "Estupefaciente",
			"custom_requires_prescription_retention": 0
		}.get(x, default)
		
		mock_customer = MagicMock()
		mock_customer.customer_name = "Cliente Test"
		mock_customer.get.side_effect = lambda x, default=None: {
			"customer_name": "Cliente Test",
			"custom_rut": None
		}.get(x, default)
		
		with patch('frappe.get_doc') as mock_get_doc:
			mock_get_doc.side_effect = [mock_item_doc1, mock_item_doc2, mock_customer]
			with patch('frappe.throw') as mock_throw:
				validate_patient_data_required(self.invoice)
				# No debe lanzar error si tiene nombre
				mock_throw.assert_not_called()


if __name__ == "__main__":
	unittest.main()

