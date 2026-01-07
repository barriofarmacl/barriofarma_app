# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para validaciones de devoluciones (Story 4.5)
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import getdate, today, add_days, date_diff
from barriofarma_app.barriofarma_app.validations.returns import (
	validate_return_requirements,
	validate_return_permissions
)


class TestReturnsValidation(unittest.TestCase):
	def setUp(self):
		self.return_invoice = MagicMock()
		self.return_invoice.is_return = 1
		self.return_invoice.items = []
		self.return_invoice.posting_date = today()
		self.return_invoice.return_against = "SINV-001"
		self.return_invoice.custom_return_reason = "Producto defectuoso"

	@patch('frappe.throw')
	@patch('frappe.msgprint')
	def test_motivo_devolucion_obligatorio(self, mock_msgprint, mock_throw):
		"""Test: Motivo de devolución es obligatorio"""
		self.return_invoice.get = lambda key, default=None: None if key == "custom_return_reason" else getattr(self.return_invoice, key, default)
		self.return_invoice.custom_return_reason = None
		
		validate_return_requirements(self.return_invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("motivo de devolución es obligatorio", call_args.lower())

	@patch('frappe.throw')
	@patch('frappe.msgprint')
	def test_motivo_devolucion_vacio_lanza_error(self, mock_msgprint, mock_throw):
		"""Test: Motivo de devolución vacío lanza error"""
		self.return_invoice.get = lambda key, default=None: "   " if key == "custom_return_reason" else getattr(self.return_invoice, key, default)
		self.return_invoice.custom_return_reason = "   "
		
		validate_return_requirements(self.return_invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("motivo de devolución es obligatorio", call_args.lower())

	@patch('frappe.throw')
	@patch('frappe.msgprint')
	@patch('frappe.db.get_value')
	def test_devolucion_dentro_plazo_no_lanza_error(self, mock_get_value, mock_msgprint, mock_throw):
		"""Test: Devolución dentro de plazo (15 días) no lanza error"""
		# Venta original hace 15 días
		original_date = add_days(today(), -15)
		mock_get_value.return_value = original_date
		
		validate_return_requirements(self.return_invoice)
		
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.msgprint')
	@patch('frappe.db.get_value')
	def test_devolucion_fuera_plazo_lanza_error(self, mock_get_value, mock_msgprint, mock_throw):
		"""Test: Devolución fuera de plazo (35 días) lanza error"""
		# Venta original hace 35 días
		original_date = add_days(today(), -35)
		mock_get_value.return_value = original_date
		
		validate_return_requirements(self.return_invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("excede el plazo permitido", call_args)

	@patch('frappe.throw')
	@patch('frappe.msgprint')
	@patch('frappe.db.get_value')
	@patch('frappe.db.exists', return_value=True)
	@patch('frappe.get_doc')
	def test_productos_vencidos_muestra_advertencia(self, mock_get_doc, mock_db_exists, mock_get_value, mock_msgprint, mock_throw):
		"""Test: Productos vencidos en devolución muestran advertencia pero no bloquean"""
		# Venta original hace 10 días
		original_date = add_days(today(), -10)
		mock_get_value.return_value = original_date
		
		# Item con batch vencido
		item = MagicMock()
		item.item_code = "ITEM-001"
		item.batch_no = "BATCH-001"
		item.get = lambda key, default=None: getattr(item, key, default)
		self.return_invoice.items = [item]
		
		# Batch vencido (hace 5 días)
		mock_batch = MagicMock()
		mock_batch.expiry_date = add_days(today(), -5)
		mock_batch.get = lambda key, default=None: getattr(mock_batch, key, default)
		
		mock_get_doc.return_value = mock_batch
		
		validate_return_requirements(self.return_invoice)
		
		# No debe lanzar error, solo advertencia
		mock_throw.assert_not_called()
		# Debe mostrar advertencia
		mock_msgprint.assert_called_once()
		call_args = mock_msgprint.call_args
		self.assertEqual(call_args[1]['indicator'], "orange")

	@patch('frappe.throw')
	@patch('frappe.msgprint')
	def test_no_es_devolucion_no_valida(self, mock_msgprint, mock_throw):
		"""Test: Si no es devolución, no se ejecutan validaciones"""
		self.return_invoice.is_return = 0
		
		validate_return_requirements(self.return_invoice)
		
		mock_throw.assert_not_called()
		mock_msgprint.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.get_roles')
	def test_usuario_sin_permisos_lanza_error(self, mock_get_roles, mock_throw):
		"""Test: Usuario sin permisos no puede realizar devoluciones"""
		mock_get_roles.return_value = ["Sales User"]  # Rol no permitido
		
		validate_return_permissions(self.return_invoice)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("No tiene permisos para realizar devoluciones", call_args)

	@patch('frappe.throw')
	@patch('frappe.get_roles')
	def test_farmaceutico_puede_devolver(self, mock_get_roles, mock_throw):
		"""Test: Farmacéutico puede realizar devoluciones"""
		mock_get_roles.return_value = ["Farmacéutico"]
		
		validate_return_permissions(self.return_invoice)
		
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.get_roles')
	def test_system_manager_puede_devolver(self, mock_get_roles, mock_throw):
		"""Test: System Manager puede realizar devoluciones"""
		mock_get_roles.return_value = ["System Manager"]
		
		validate_return_permissions(self.return_invoice)
		
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	@patch('frappe.msgprint')
	@patch('frappe.db.get_value')
	def test_devolucion_sin_return_against_no_valida_plazo(self, mock_get_value, mock_msgprint, mock_throw):
		"""Test: Devolución sin return_against no valida plazo"""
		self.return_invoice.get = lambda key, default=None: None if key == "return_against" else getattr(self.return_invoice, key, default)
		self.return_invoice.return_against = None
		
		validate_return_requirements(self.return_invoice)
		
		# No debe llamar a get_value si no hay return_against
		# Pero puede llamarse si hay items con batches, así que solo verificamos que no lance error por plazo
		mock_throw.assert_not_called()

