# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para validaciones de trazabilidad
Story 2.1: Validación de Trazabilidad Completa en Ventas

Objetivo: Validar que los productos con has_batch_no=1 requieran batch_no
y que el Batch tenga expiry_date antes de permitir venta.

- validate_batch_required_for_sale()

Cobertura: 100% de funcionalidad de validación de trazabilidad
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import frappe


class MockItem:
    """Mock de un item de Sales Invoice"""
    def __init__(self, **kwargs):
        self._data = {}
        for key, value in kwargs.items():
            self._data[key] = value
            setattr(self, key, value)
    
    def get(self, key, default=None):
        return self._data.get(key, default)


class MockInvoice:
    """Mock de Sales Invoice (API compatible con Document.get)."""

    def __init__(self, items=None):
        self.items = items or []

    def get(self, key, default=None):
        if key == "items":
            return self.items
        return getattr(self, key, default)


class TestBatchRequiredForSale(unittest.TestCase):
    """
    Tests para validate_batch_required_for_sale()
    
    Verifica que items con has_batch_no=1 requieran batch_no y expiry_date
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.validations.traceability import validate_batch_required_for_sale
        self.validate_func = validate_batch_required_for_sale
    
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.throw')
    def test_item_sin_batch_no_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Item con has_batch_no=1 sin batch_no debe lanzar error"""
        mock_exists.return_value = True
        mock_throw.side_effect = frappe.ValidationError("Lote requerido")
        
        mock_item_doc = Mock()
        mock_item_doc.get.return_value = 1  # has_batch_no=1
        mock_get_doc.return_value = mock_item_doc
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                batch_no=None
            )
        ])
        
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("lote", call_args[0][0].lower())
        self.assertIn("batch_no", call_args[0][0].lower())
    
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.throw')
    def test_batch_no_existe_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Batch que no existe debe lanzar error"""
        mock_exists.side_effect = lambda doctype, name: {
            ("Item", "ITEM-001"): True,
            ("Batch", "BATCH-001"): False
        }.get((doctype, name))
        mock_throw.side_effect = frappe.ValidationError("Lote inválido")
        
        mock_item_doc = Mock()
        mock_item_doc.get.return_value = 1  # has_batch_no=1
        mock_get_doc.return_value = mock_item_doc
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                batch_no="BATCH-001"
            )
        ])
        
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("no existe", call_args[0][0].lower())
    
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.throw')
    def test_batch_sin_expiry_date_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Batch sin expiry_date debe lanzar error"""
        def get_doc_side_effect(doctype, name):
            if doctype == "Item":
                mock_item = Mock()
                mock_item.get.return_value = 1  # has_batch_no=1
                return mock_item
            elif doctype == "Batch":
                mock_batch = Mock()
                mock_batch.get.return_value = None  # expiry_date=None
                return mock_batch
            return Mock()
        
        mock_exists.side_effect = lambda doctype, name: {
            ("Item", "ITEM-001"): True,
            ("Batch", "BATCH-001"): True
        }.get((doctype, name))
        mock_get_doc.side_effect = get_doc_side_effect
        mock_throw.side_effect = frappe.ValidationError("Fecha de caducidad requerida")
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                batch_no="BATCH-001"
            )
        ])
        
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("fecha de caducidad", call_args[0][0].lower())
        self.assertIn("expiry_date", call_args[0][0].lower())
    
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.throw')
    def test_item_con_batch_y_expiry_date_no_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Item con batch_no y expiry_date no debe lanzar error"""
        def get_doc_side_effect(doctype, name):
            if doctype == "Item":
                mock_item = Mock()
                mock_item.get.return_value = 1  # has_batch_no=1
                return mock_item
            elif doctype == "Batch":
                mock_batch = Mock()
                mock_batch.get.return_value = "2026-12-31"  # expiry_date presente
                return mock_batch
            return Mock()
        
        mock_exists.side_effect = lambda doctype, name: {
            ("Item", "ITEM-001"): True,
            ("Batch", "BATCH-001"): True
        }.get((doctype, name))
        mock_get_doc.side_effect = get_doc_side_effect
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                batch_no="BATCH-001"
            )
        ])
        
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.throw')
    def test_item_sin_has_batch_no_no_valida(self, mock_throw, mock_exists, mock_get_doc):
        """Item sin has_batch_no=1 no debe validar batch_no"""
        mock_exists.return_value = True
        
        mock_item_doc = Mock()
        mock_item_doc.get.return_value = 0  # has_batch_no=0
        mock_get_doc.return_value = mock_item_doc
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                batch_no=None
            )
        ])
        
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.throw')
    def test_multiples_items_con_validaciones(self, mock_throw, mock_exists, mock_get_doc):
        """Múltiples items deben validarse todos"""
        def get_doc_side_effect(doctype, name):
            if doctype == "Item":
                mock_item = Mock()
                if name == "ITEM-001":
                    mock_item.get.return_value = 1  # has_batch_no=1
                else:
                    mock_item.get.return_value = 0  # has_batch_no=0
                return mock_item
            elif doctype == "Batch":
                mock_batch = Mock()
                mock_batch.get.return_value = "2026-12-31"
                return mock_batch
            return Mock()
        
        mock_exists.side_effect = lambda doctype, name: {
            ("Item", "ITEM-001"): True,
            ("Item", "ITEM-002"): True,
            ("Batch", "BATCH-001"): True
        }.get((doctype, name))
        mock_get_doc.side_effect = get_doc_side_effect
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                batch_no="BATCH-001"
            ),
            MockItem(
                item_code="ITEM-002",
                batch_no=None
            )
        ])
        
        self.validate_func(invoice)
        
        # Solo debe validar ITEM-001 (has_batch_no=1)
        # ITEM-002 no requiere validación
        mock_throw.assert_not_called()
    
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.throw')
    def test_item_no_existe_no_valida(self, mock_throw, mock_exists, mock_get_doc):
        """Item que no existe no debe validar"""
        mock_exists.return_value = False
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-NONEXISTENT",
                batch_no=None
            )
        ])
        
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
        mock_get_doc.assert_not_called()
    
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.validations.traceability.frappe.db.exists')
    def test_sin_items_no_valida(self, mock_exists, mock_get_doc):
        """Sin items no debe validar"""
        invoice = MockInvoice(items=[])
        
        self.validate_func(invoice)
        
        mock_exists.assert_not_called()
        mock_get_doc.assert_not_called()


if __name__ == '__main__':
    unittest.main()

