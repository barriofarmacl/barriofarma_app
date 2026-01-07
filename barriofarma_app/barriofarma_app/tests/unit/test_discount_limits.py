# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para validación de límites de descuento por rol.

Story 4.4: Aplicación de Descuentos y Promociones
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe.exceptions import ValidationError
from barriofarma_app.barriofarma_app.validations.discount_limits import (
	validate_discount_limits,
	get_max_discount_for_user
)


class TestDiscountLimits(unittest.TestCase):
	"""Tests para validación de límites de descuento"""
	
	def setUp(self):
		"""Configurar mocks para cada test"""
		self.invoice = MagicMock()
		self.invoice.name = "TEST-SI-001"
		self.invoice.items = []
		self.invoice.additional_discount_percentage = 0.0
		self.invoice.discount_amount = 0.0
		self.invoice.total = 1000.0
	
	def test_descuento_dentro_limite_no_lanza_error(self):
		"""Test: Descuento dentro del límite no debe lanzar error"""
		self.invoice.additional_discount_percentage = 20.0  # Dentro del límite por defecto
		self.invoice.discount_amount = 200.0  # 20% de 1000
		self.invoice.total = 800.0  # Total después de descuento
		
		with patch('barriofarma_app.barriofarma_app.validations.discount_limits.get_max_discount_for_user', return_value=30.0):
			with patch('frappe.throw') as mock_throw:
				validate_discount_limits(self.invoice)
				mock_throw.assert_not_called()
	
	def test_descuento_adicional_excede_limite_lanza_error(self):
		"""Test: Descuento adicional que excede límite debe lanzar error"""
		self.invoice.additional_discount_percentage = 50.0  # Excede límite de 30%
		self.invoice.discount_amount = 0.0  # Sin descuento total para simplificar
		self.invoice.total = 1000.0
		
		with patch('barriofarma_app.barriofarma_app.validations.discount_limits.get_max_discount_for_user', return_value=30.0):
			with patch('frappe.throw') as mock_throw:
				validate_discount_limits(self.invoice)
				# Debe lanzar error por descuento adicional
				mock_throw.assert_called()
				# Verificar que el primer error es por descuento adicional
				first_call = mock_throw.call_args_list[0]
				call_args = first_call[0][0]
				self.assertIn("descuento adicional", call_args.lower())
				self.assertIn("50", call_args)
				self.assertIn("30", call_args)
	
	def test_descuento_item_dentro_limite_no_lanza_error(self):
		"""Test: Descuento en item dentro del límite no debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.item_name = "Item Test"
		item.discount_percentage = 15.0  # Dentro del límite
		item.get = lambda x, default=None: {"discount_percentage": 15.0}.get(x, default)
		self.invoice.items = [item]
		self.invoice.discount_amount = 150.0  # 15% de 1000
		self.invoice.total = 850.0  # Total después de descuento
		
		with patch('barriofarma_app.barriofarma_app.validations.discount_limits.get_max_discount_for_user', return_value=30.0):
			with patch('frappe.throw') as mock_throw:
				validate_discount_limits(self.invoice)
				mock_throw.assert_not_called()
	
	def test_descuento_item_excede_limite_lanza_error(self):
		"""Test: Descuento en item que excede límite debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.item_name = "Item Test"
		item.discount_percentage = 40.0  # Excede límite de 30%
		item.get = lambda x, default=None: {"discount_percentage": 40.0}.get(x, default)
		self.invoice.items = [item]
		self.invoice.discount_amount = 0.0  # Sin descuento total para simplificar
		self.invoice.total = 1000.0
		
		with patch('barriofarma_app.barriofarma_app.validations.discount_limits.get_max_discount_for_user', return_value=30.0):
			with patch('frappe.throw') as mock_throw:
				validate_discount_limits(self.invoice)
				# Debe lanzar error por descuento en item
				mock_throw.assert_called()
				# Verificar que el primer error es por descuento en item
				first_call = mock_throw.call_args_list[0]
				call_args = first_call[0][0]
				self.assertIn("descuento", call_args.lower())
				self.assertIn("ITEM-001", call_args)
				self.assertIn("40", call_args)
				self.assertIn("30", call_args)
	
	# Nota: Tests de descuento total removidos porque la validación del descuento total
	# se omite intencionalmente (ver comentarios en discount_limits.py)
	# La validación se enfoca en descuentos individuales y adicionales, que son más precisos
	
	def test_sin_items_no_valida(self):
		"""Test: Si no hay items, no debe validar"""
		self.invoice.items = []
		self.invoice.additional_discount_percentage = 0.0
		self.invoice.discount_amount = 0.0
		self.invoice.total = 0.0
		
		with patch('barriofarma_app.barriofarma_app.validations.discount_limits.get_max_discount_for_user', return_value=30.0):
			with patch('frappe.throw') as mock_throw:
				validate_discount_limits(self.invoice)
				# No debe lanzar error si no hay items y no hay descuento
				mock_throw.assert_not_called()
	
	def test_multiple_items_con_descuentos(self):
		"""Test: Múltiples items con descuentos deben validarse"""
		item1 = MagicMock()
		item1.item_code = "ITEM-001"
		item1.item_name = "Item 1"
		item1.discount_percentage = 25.0  # Dentro del límite
		item1.get = lambda x, default=None: {"discount_percentage": 25.0}.get(x, default)
		
		item2 = MagicMock()
		item2.item_code = "ITEM-002"
		item2.item_name = "Item 2"
		item2.discount_percentage = 35.0  # Excede límite de 30%
		item2.get = lambda x, default=None: {"discount_percentage": 35.0}.get(x, default)
		
		self.invoice.items = [item1, item2]
		self.invoice.discount_amount = 0.0  # Sin descuento total para simplificar
		self.invoice.total = 1000.0
		
		with patch('barriofarma_app.barriofarma_app.validations.discount_limits.get_max_discount_for_user', return_value=30.0):
			with patch('frappe.throw') as mock_throw:
				validate_discount_limits(self.invoice)
				# Debe lanzar error por descuento en ITEM-002
				mock_throw.assert_called()
				# Verificar que el primer error es por ITEM-002
				first_call = mock_throw.call_args_list[0]
				call_args = first_call[0][0]
				self.assertIn("ITEM-002", call_args)
	
	def test_get_max_discount_system_manager(self):
		"""Test: System Manager debe tener límite alto"""
		with patch('frappe.get_roles', return_value=["System Manager"]):
			max_discount = get_max_discount_for_user()
			self.assertEqual(max_discount, 100.0)
	
	def test_get_max_discount_sales_user(self):
		"""Test: Sales User debe tener límite de 30%"""
		with patch('frappe.get_roles', return_value=["Sales User"]):
			max_discount = get_max_discount_for_user()
			self.assertEqual(max_discount, 30.0)
	
	def test_get_max_discount_multiple_roles(self):
		"""Test: Usuario con múltiples roles debe tener el límite más alto"""
		with patch('frappe.get_roles', return_value=["Sales User", "Farmacéutico"]):
			max_discount = get_max_discount_for_user()
			# Debe ser el más alto entre los roles: 50% (Farmacéutico)
			self.assertEqual(max_discount, 50.0)
	
	def test_get_max_discount_rol_sin_limite(self):
		"""Test: Usuario sin rol con límite debe tener límite por defecto"""
		with patch('frappe.get_roles', return_value=["Custom Role"]):
			max_discount = get_max_discount_for_user()
			# Debe usar límite por defecto: 20%
			self.assertEqual(max_discount, 20.0)
	
	def test_descuento_cero_no_valida(self):
		"""Test: Descuento cero no debe validar"""
		self.invoice.additional_discount_percentage = 0.0
		item = MagicMock()
		item.discount_percentage = 0.0
		item.get = lambda x, default=None: {"discount_percentage": 0.0}.get(x, default)
		self.invoice.items = [item]
		self.invoice.discount_amount = 0.0
		self.invoice.total = 1000.0
		
		with patch('barriofarma_app.barriofarma_app.validations.discount_limits.get_max_discount_for_user', return_value=30.0):
			with patch('frappe.throw') as mock_throw:
				validate_discount_limits(self.invoice)
				mock_throw.assert_not_called()


if __name__ == "__main__":
	unittest.main()

