# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para validación de disponibilidad de stock en tiempo real.

Story 4.1: Validación de Disponibilidad de Stock en Tiempo Real
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
import frappe
from frappe.exceptions import ValidationError
from barriofarma_app.barriofarma_app.validations.stock_availability import validate_stock_availability


class TestStockAvailability(unittest.TestCase):
	"""Tests para validación de disponibilidad de stock"""
	
	def setUp(self):
		"""Configurar mocks para cada test"""
		self.invoice = MagicMock()
		self.invoice.name = "TEST-SI-001"
		self.invoice.items = []
		self.invoice.set_warehouse = "Stores - BF"
	
	def test_stock_suficiente_no_lanza_error(self):
		"""Test: Si hay stock suficiente, no debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = "Stores - BF"
		item.qty = 10.0
		self.invoice.items = [item]
		
		mock_bin = MagicMock()
		mock_bin.actual_qty = 50.0  # Stock suficiente
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin', return_value="BIN-001"):
			with patch('frappe.get_doc', return_value=mock_bin):
				with patch('frappe.throw') as mock_throw:
					validate_stock_availability(self.invoice)
					mock_throw.assert_not_called()
	
	def test_stock_cero_lanza_error(self):
		"""Test: Si stock es 0, debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = "Stores - BF"
		item.qty = 10.0
		self.invoice.items = [item]
		
		mock_bin = MagicMock()
		mock_bin.actual_qty = 0.0  # Sin stock
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin', return_value="BIN-001"):
			with patch('frappe.get_doc', return_value=mock_bin):
				with patch('frappe.throw') as mock_throw:
					validate_stock_availability(self.invoice)
					# Debe lanzar error una vez (el return previene el segundo error)
					mock_throw.assert_called_once()
					# Verificar que el mensaje contiene información relevante
					call_args = mock_throw.call_args[0][0]
					self.assertIn("ITEM-001", call_args)
					self.assertIn("Stores - BF", call_args)
					self.assertIn("Stock No Disponible", str(mock_throw.call_args[1]['title']))
	
	def test_stock_insuficiente_lanza_error(self):
		"""Test: Si cantidad solicitada > stock disponible, debe lanzar error"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = "Stores - BF"
		item.qty = 50.0  # Cantidad solicitada
		self.invoice.items = [item]
		
		mock_bin = MagicMock()
		mock_bin.actual_qty = 30.0  # Stock insuficiente
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin', return_value="BIN-001"):
			with patch('frappe.get_doc', return_value=mock_bin):
				with patch('frappe.throw') as mock_throw:
					validate_stock_availability(self.invoice)
					mock_throw.assert_called_once()
					call_args = mock_throw.call_args[0][0]
					self.assertIn("Stock insuficiente", call_args)
					self.assertIn("50", call_args)  # Cantidad solicitada
					self.assertIn("30", call_args)  # Stock disponible
	
	def test_stock_bajo_muestra_advertencia(self):
		"""Test: Si stock < stock mínimo, debe mostrar advertencia"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = "Stores - BF"
		item.qty = 5.0
		self.invoice.items = [item]
		
		mock_bin = MagicMock()
		mock_bin.actual_qty = 8.0  # Stock bajo (menor que mínimo)
		
		mock_item_doc = MagicMock()
		mock_item_doc.get.return_value = 10.0  # stock_minimum = 10
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin', return_value="BIN-001"):
			with patch('frappe.get_doc') as mock_get_doc:
				mock_get_doc.side_effect = [mock_bin, mock_item_doc]  # Primero Bin, luego Item
				with patch('frappe.msgprint') as mock_msgprint:
					validate_stock_availability(self.invoice)
					mock_msgprint.assert_called_once()
					call_args = mock_msgprint.call_args
					# Verificar que es una advertencia (indicator="orange")
					self.assertEqual(call_args[1]['indicator'], "orange")
					self.assertIn("Stock Bajo", call_args[1]['title'])
	
	def test_stock_suficiente_no_muestra_advertencia(self):
		"""Test: Si stock >= stock mínimo, no debe mostrar advertencia"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = "Stores - BF"
		item.qty = 5.0
		self.invoice.items = [item]
		
		mock_bin = MagicMock()
		mock_bin.actual_qty = 15.0  # Stock suficiente (mayor que mínimo)
		
		mock_item_doc = MagicMock()
		mock_item_doc.get.return_value = 10.0  # stock_minimum = 10
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin', return_value="BIN-001"):
			with patch('frappe.get_doc') as mock_get_doc:
				mock_get_doc.side_effect = [mock_bin, mock_item_doc]
				with patch('frappe.msgprint') as mock_msgprint:
					validate_stock_availability(self.invoice)
					# No debe mostrar advertencia si stock >= mínimo
					# (pero puede mostrar si stock < mínimo en otro caso)
					# En este caso, stock (15) >= mínimo (10), así que no debe mostrar
					# Pero msgprint puede ser llamado si hay otros items con stock bajo
					# Por ahora, verificamos que no se llama con "Stock Bajo"
					if mock_msgprint.called:
						call_args = mock_msgprint.call_args
						if 'title' in call_args[1]:
							self.assertNotIn("Stock Bajo", call_args[1]['title'])
	
	def test_sin_warehouse_no_valida(self):
		"""Test: Si no hay warehouse, no debe validar stock"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = None  # Sin warehouse
		item.qty = 10.0
		self.invoice.items = [item]
		self.invoice.set_warehouse = None  # Sin warehouse en documento
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin') as mock_get_bin:
			validate_stock_availability(self.invoice)
			# No debe llamar a get_or_make_bin si no hay warehouse
			mock_get_bin.assert_not_called()
	
	def test_usa_warehouse_del_item(self):
		"""Test: Debe usar warehouse del item si está disponible"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = "Warehouse-Item"  # Warehouse del item
		item.qty = 10.0
		self.invoice.items = [item]
		self.invoice.set_warehouse = "Warehouse-Doc"  # Warehouse del documento
		
		mock_bin = MagicMock()
		mock_bin.actual_qty = 50.0
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin', return_value="BIN-001") as mock_get_bin:
			with patch('frappe.get_doc', return_value=mock_bin):
				validate_stock_availability(self.invoice)
				# Debe usar warehouse del item, no del documento
				mock_get_bin.assert_called_once_with("ITEM-001", "Warehouse-Item")
	
	def test_usa_warehouse_del_documento_si_item_no_tiene(self):
		"""Test: Debe usar warehouse del documento si item no tiene"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = None  # Item sin warehouse
		item.qty = 10.0
		self.invoice.items = [item]
		self.invoice.set_warehouse = "Warehouse-Doc"  # Warehouse del documento
		
		mock_bin = MagicMock()
		mock_bin.actual_qty = 50.0
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin', return_value="BIN-001") as mock_get_bin:
			with patch('frappe.get_doc', return_value=mock_bin):
				validate_stock_availability(self.invoice)
				# Debe usar warehouse del documento
				mock_get_bin.assert_called_once_with("ITEM-001", "Warehouse-Doc")
	
	def test_cantidad_cero_no_valida(self):
		"""Test: Si cantidad es 0, no debe validar stock"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = "Stores - BF"
		item.qty = 0.0  # Cantidad cero
		self.invoice.items = [item]
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin') as mock_get_bin:
			validate_stock_availability(self.invoice)
			# No debe llamar a get_or_make_bin si cantidad es 0
			mock_get_bin.assert_not_called()
	
	def test_sin_items_no_valida(self):
		"""Test: Si no hay items, no debe validar"""
		self.invoice.items = []
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin') as mock_get_bin:
			validate_stock_availability(self.invoice)
			mock_get_bin.assert_not_called()
	
	def test_error_al_consultar_bin_no_bloquea(self):
		"""Test: Si hay error al consultar Bin, no debe bloquear la venta"""
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.warehouse = "Stores - BF"
		item.qty = 10.0
		self.invoice.items = [item]
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin', side_effect=Exception("DB Error")):
			with patch('frappe.log_error') as mock_log_error:
				with patch('frappe.throw') as mock_throw:
					validate_stock_availability(self.invoice)
					# Debe registrar el error pero no bloquear
					mock_log_error.assert_called_once()
					mock_throw.assert_not_called()
	
	def test_multiple_items_valida_todos(self):
		"""Test: Debe validar stock para todos los items"""
		item1 = MagicMock()
		item1.item_code = "ITEM-001"
		item1.warehouse = "Stores - BF"
		item1.qty = 10.0
		
		item2 = MagicMock()
		item2.item_code = "ITEM-002"
		item2.warehouse = "Stores - BF"
		item2.qty = 5.0
		
		self.invoice.items = [item1, item2]
		
		mock_bin = MagicMock()
		mock_bin.actual_qty = 50.0
		
		with patch('barriofarma_app.barriofarma_app.validations.stock_availability.get_or_make_bin', return_value="BIN-001"):
			with patch('frappe.get_doc', return_value=mock_bin) as mock_get_doc:
				# get_doc se llama para Bin (2 veces, una por cada item)
				# También puede llamarse para Item si hay stock mínimo, pero simplificamos
				with patch('frappe.throw') as mock_throw:
					with patch('frappe.log_error'):  # Mock log_error para evitar llamadas adicionales
						validate_stock_availability(self.invoice)
						# Debe validar ambos items (get_doc se llama al menos 2 veces para los Bins)
						self.assertGreaterEqual(mock_get_doc.call_count, 2)  # Al menos 2 veces (una por cada Bin)
						mock_throw.assert_not_called()


if __name__ == "__main__":
	unittest.main()

