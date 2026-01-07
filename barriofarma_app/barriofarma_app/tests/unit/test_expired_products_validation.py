# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para la validación de productos vencidos (FR12)
Story 1.3: Validación de Productos Vencidos en Ventas

Objetivo: Validar que el sistema prevenga la venta de productos vencidos
- validate_expired_products_in_invoice()

Cobertura: 100% de escenarios de validación
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, timedelta
import frappe

# Módulo donde se importa today() para hacer patch correctamente
VALIDATION_MODULE = 'barriofarma_app.barriofarma_app.validations.expired_products'


class MockItem:
    """Mock de un item de factura"""
    def __init__(self, item_code, batch_no=None):
        self.item_code = item_code
        self.batch_no = batch_no
    
    def get(self, key, default=None):
        return getattr(self, key, default)


class MockInvoice:
    """Mock de una factura (Sales Invoice o POS Invoice)"""
    def __init__(self, items=None):
        self.items = items or []
    
    def get(self, key, default=None):
        return getattr(self, key, default)


class TestExpiredProductsValidation(unittest.TestCase):
    """
    Tests para validate_expired_products_in_invoice()
    
    Escenarios:
    - Producto vencido → error
    - Producto no vencido → OK
    - Producto sin lote → OK (no aplica validación)
    - Batch sin fecha de caducidad → OK
    - Batch no existe → OK (no bloquea)
    - Factura sin items → OK
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.validations.expired_products import validate_expired_products_in_invoice
        self.validate_func = validate_expired_products_in_invoice
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_producto_vencido_lanza_error(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """Producto con fecha de caducidad vencida debe lanzar error"""
        # Configurar fecha actual
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        mock_throw.side_effect = frappe.ValidationError("Producto vencido")
        
        # Configurar batch vencido (caducó hace 30 días)
        mock_batch = Mock()
        mock_batch.get.return_value = date(2025, 12, 1)  # Fecha pasada
        mock_get_doc.return_value = mock_batch
        
        # Crear factura con producto vencido
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="BATCH-001")
        ])
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        # Verificar que frappe.throw fue llamado
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("vencido", call_args[0][0])
        self.assertIn("ITEM-001", call_args[0][0])
        self.assertIn("BATCH-001", call_args[0][0])
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_producto_no_vencido_no_lanza_error(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """Producto con fecha de caducidad futura no debe lanzar error"""
        # Configurar fecha actual
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        
        # Configurar batch no vencido (caduca en 6 meses)
        mock_batch = Mock()
        mock_batch.get.return_value = date(2026, 7, 1)  # Fecha futura
        mock_get_doc.return_value = mock_batch
        
        # Crear factura con producto no vencido
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="BATCH-001")
        ])
        
        # No debe lanzar error
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_producto_vence_hoy_no_lanza_error(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """Producto que vence hoy (mismo día) no debe lanzar error"""
        # Configurar fecha actual
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        
        # Configurar batch que vence hoy
        mock_batch = Mock()
        mock_batch.get.return_value = date(2026, 1, 7)  # Mismo día
        mock_get_doc.return_value = mock_batch
        
        # Crear factura con producto que vence hoy
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="BATCH-001")
        ])
        
        # No debe lanzar error (vence hoy pero no está vencido)
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    def test_producto_sin_lote_no_valida(self, mock_throw):
        """Producto sin batch_no no debe validar caducidad"""
        # Crear factura con producto sin lote
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no=None)
        ])
        
        # No debe lanzar error
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_batch_sin_fecha_caducidad_no_valida(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """Batch sin fecha de caducidad no debe validar"""
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        
        # Configurar batch sin fecha de caducidad
        mock_batch = Mock()
        mock_batch.get.return_value = None  # Sin fecha
        mock_get_doc.return_value = mock_batch
        
        # Crear factura
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="BATCH-001")
        ])
        
        # No debe lanzar error
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_batch_no_existe_no_bloquea(self, mock_getdate, mock_today, mock_throw, mock_exists):
        """Batch que no existe no debe bloquear la venta"""
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = False
        
        # Crear factura con batch que no existe
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="BATCH-NONEXISTENT")
        ])
        
        # No debe lanzar error (el batch será creado o hay otro problema)
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    def test_factura_sin_items_no_valida(self, mock_throw):
        """Factura sin items no debe validar"""
        invoice = MockInvoice(items=[])
        
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    def test_factura_items_none_no_valida(self, mock_throw):
        """Factura con items=None no debe fallar"""
        invoice = MockInvoice(items=None)
        
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_multiples_items_uno_vencido_lanza_error(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """Factura con múltiples items, uno vencido debe lanzar error"""
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        mock_throw.side_effect = frappe.ValidationError("Producto vencido")
        
        # Configurar batches
        def get_batch(doctype, name):
            mock_batch = Mock()
            if name == "BATCH-EXPIRED":
                mock_batch.get.return_value = date(2025, 12, 1)  # Vencido
            else:
                mock_batch.get.return_value = date(2026, 12, 1)  # No vencido
            return mock_batch
        
        mock_get_doc.side_effect = get_batch
        
        # Crear factura con múltiples items
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="BATCH-OK"),
            MockItem(item_code="ITEM-002", batch_no="BATCH-EXPIRED"),
            MockItem(item_code="ITEM-003", batch_no=None)
        ])
        
        # Debe lanzar error por el producto vencido
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        # Verificar que el error menciona el producto vencido
        call_args = mock_throw.call_args
        self.assertIn("ITEM-002", call_args[0][0])
        self.assertIn("BATCH-EXPIRED", call_args[0][0])
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_multiples_items_ninguno_vencido_no_lanza_error(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """Factura con múltiples items, ninguno vencido no debe lanzar error"""
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        
        # Configurar batch no vencido
        mock_batch = Mock()
        mock_batch.get.return_value = date(2026, 12, 1)  # No vencido
        mock_get_doc.return_value = mock_batch
        
        # Crear factura con múltiples items
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="BATCH-001"),
            MockItem(item_code="ITEM-002", batch_no="BATCH-002"),
            MockItem(item_code="ITEM-003", batch_no=None)  # Sin lote
        ])
        
        # No debe lanzar error
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()


class TestErrorMessageFormat(unittest.TestCase):
    """
    Tests para verificar el formato del mensaje de error
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.validations.expired_products import validate_expired_products_in_invoice
        self.validate_func = validate_expired_products_in_invoice
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_mensaje_error_contiene_item_code(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """El mensaje de error debe contener el código del item"""
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        mock_throw.side_effect = frappe.ValidationError("error")
        
        mock_batch = Mock()
        mock_batch.get.return_value = date(2025, 12, 1)
        mock_get_doc.return_value = mock_batch
        
        invoice = MockInvoice(items=[
            MockItem(item_code="PARACETAMOL-500MG", batch_no="LOT-2025-001")
        ])
        
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        call_args = mock_throw.call_args
        self.assertIn("PARACETAMOL-500MG", call_args[0][0])
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_mensaje_error_contiene_batch_no(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """El mensaje de error debe contener el número de lote"""
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        mock_throw.side_effect = frappe.ValidationError("error")
        
        mock_batch = Mock()
        mock_batch.get.return_value = date(2025, 12, 1)
        mock_get_doc.return_value = mock_batch
        
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="LOT-SPECIAL-2025")
        ])
        
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        call_args = mock_throw.call_args
        self.assertIn("LOT-SPECIAL-2025", call_args[0][0])
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_mensaje_error_contiene_fecha_formateada(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """El mensaje de error debe contener la fecha de caducidad formateada"""
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        mock_throw.side_effect = frappe.ValidationError("error")
        
        mock_batch = Mock()
        mock_batch.get.return_value = date(2025, 6, 15)  # 15/06/2025
        mock_get_doc.return_value = mock_batch
        
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="BATCH-001")
        ])
        
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        call_args = mock_throw.call_args
        # Verificar que la fecha está en formato dd/mm/yyyy
        self.assertIn("15/06/2025", call_args[0][0])
    
    @patch(f'{VALIDATION_MODULE}.frappe.get_doc')
    @patch(f'{VALIDATION_MODULE}.frappe.db.exists')
    @patch(f'{VALIDATION_MODULE}.frappe.throw')
    @patch(f'{VALIDATION_MODULE}.today')
    @patch(f'{VALIDATION_MODULE}.getdate')
    def test_mensaje_error_tiene_titulo_apropiado(self, mock_getdate, mock_today, mock_throw, mock_exists, mock_get_doc):
        """El mensaje de error debe tener un título apropiado"""
        mock_today.return_value = "2026-01-07"
        mock_getdate.side_effect = lambda x: date(2026, 1, 7) if x == "2026-01-07" else x
        mock_exists.return_value = True
        mock_throw.side_effect = frappe.ValidationError("error")
        
        mock_batch = Mock()
        mock_batch.get.return_value = date(2025, 12, 1)
        mock_get_doc.return_value = mock_batch
        
        invoice = MockInvoice(items=[
            MockItem(item_code="ITEM-001", batch_no="BATCH-001")
        ])
        
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        call_args = mock_throw.call_args
        # Verificar que el título contiene "Vencido"
        self.assertIn("Vencido", call_args[1].get("title", ""))


class TestPOSInvoiceHook(unittest.TestCase):
    """
    Tests para el hook de POS Invoice
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.validations.expired_products import validate_pos_invoice_expired_products
        self.validate_hook = validate_pos_invoice_expired_products
    
    @patch('barriofarma_app.barriofarma_app.validations.expired_products.validate_expired_products_in_invoice')
    def test_hook_llama_a_funcion_de_validacion(self, mock_validate):
        """El hook de POS Invoice debe llamar a la función de validación"""
        mock_doc = Mock()
        
        self.validate_hook(mock_doc, "validate")
        
        mock_validate.assert_called_once_with(mock_doc, "validate")


if __name__ == '__main__':
    unittest.main()

