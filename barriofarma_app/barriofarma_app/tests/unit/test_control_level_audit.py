# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para la auditoría de cambios en control level
Story 1.4: Auditoría de Cambios en Control Level

Objetivo: Validar que todos los cambios en control level sean registrados
con auditoría completa e inmutable.

- log_control_level_change()
- validate_control_level_change_reason()
- detect_and_log_control_level_changes()
- Control Level Change Log DocType

Cobertura: 100% de funcionalidad de auditoría
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
    """Mock de Sales Invoice"""
    def __init__(self, items=None, name="SI-001", doctype="Sales Invoice"):
        self.items = items or []
        self.name = name
        self.doctype = doctype


class TestLogControlLevelChange(unittest.TestCase):
    """
    Tests para log_control_level_change()
    
    Verifica que los cambios en control level se registren correctamente
    en Control Level Change Log
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.utils.domain.control_level_audit import log_control_level_change
        self.log_func = log_control_level_change
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.commit')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.session')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.now')
    def test_log_cambio_control_level_exitoso(self, mock_now, mock_session, mock_commit, mock_exists, mock_get_doc):
        """Registro exitoso de cambio en control level"""
        mock_now.return_value = "2026-01-07 10:00:00"
        mock_session.user = "test_user@barriofarma.cl"
        mock_exists.return_value = True
        
        mock_log_doc = Mock()
        mock_log_doc.name = "CLCL-001"
        mock_log_doc.insert = Mock()
        mock_get_doc.return_value = mock_log_doc
        
        result = self.log_func(
            item_code="ITEM-001",
            previous_control_level="None",
            new_control_level="Psicotrópico",
            reason="Corrección de clasificación según nueva normativa"
        )
        
        self.assertEqual(result, "CLCL-001")
        mock_log_doc.insert.assert_called_once_with(ignore_permissions=True)
        mock_commit.assert_called_once()
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.throw')
    def test_log_sin_motivo_lanza_error(self, mock_throw):
        """Registro sin motivo debe lanzar error"""
        mock_throw.side_effect = frappe.ValidationError("Motivo requerido")
        
        with self.assertRaises(frappe.ValidationError):
            self.log_func(
                item_code="ITEM-001",
                previous_control_level="None",
                new_control_level="Psicotrópico",
                reason=None
            )
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("motivo", call_args[0][0].lower())
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.throw')
    def test_log_motivo_vacio_lanza_error(self, mock_throw):
        """Registro con motivo vacío debe lanzar error"""
        mock_throw.side_effect = frappe.ValidationError("Motivo requerido")
        
        with self.assertRaises(frappe.ValidationError):
            self.log_func(
                item_code="ITEM-001",
                previous_control_level="None",
                new_control_level="Psicotrópico",
                reason=""
            )
        
        mock_throw.assert_called_once()
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.throw')
    def test_log_item_no_existe_lanza_error(self, mock_throw):
        """Registro para item que no existe debe lanzar error"""
        mock_throw.side_effect = frappe.ValidationError("Item inválido")
        
        with patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.exists', return_value=False):
            with self.assertRaises(frappe.ValidationError):
                self.log_func(
                    item_code="ITEM-NONEXISTENT",
                    previous_control_level="None",
                    new_control_level="Psicotrópico",
                    reason="Motivo válido"
                )
        
        mock_throw.assert_called_once()
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.commit')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.session')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.now')
    def test_log_con_referencia(self, mock_now, mock_session, mock_commit, mock_exists, mock_get_doc):
        """Registro con referencia a Sales Invoice"""
        mock_now.return_value = "2026-01-07 10:00:00"
        mock_session.user = "test_user@barriofarma.cl"
        mock_exists.return_value = True
        
        mock_log_doc = Mock()
        mock_log_doc.name = "CLCL-002"
        mock_log_doc.insert = Mock()
        mock_get_doc.return_value = mock_log_doc
        
        result = self.log_func(
            item_code="ITEM-001",
            previous_control_level="None",
            new_control_level="Estupefaciente",
            reason="Actualización según normativa",
            reference_doctype="Sales Invoice",
            reference_name="SI-001"
        )
        
        self.assertEqual(result, "CLCL-002")
        # Verificar que se pasaron los parámetros correctos
        call_args = mock_get_doc.call_args
        self.assertEqual(call_args[0][0]["reference_doctype"], "Sales Invoice")
        self.assertEqual(call_args[0][0]["reference_name"], "SI-001")


class TestValidateControlLevelChangeReason(unittest.TestCase):
    """
    Tests para validate_control_level_change_reason()
    
    Verifica que se valide correctamente la presencia del motivo
    cuando hay cambios en control level
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.utils.domain.control_level_audit import validate_control_level_change_reason
        self.validate_func = validate_control_level_change_reason
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.throw')
    def test_cambio_sin_motivo_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Cambio en control level sin motivo debe lanzar error"""
        mock_exists.return_value = True
        mock_throw.side_effect = frappe.ValidationError("Motivo requerido")
        
        mock_item_doc = Mock()
        mock_item_doc.get.return_value = "None"  # Control level actual
        mock_get_doc.return_value = mock_item_doc
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                custom_new_control_level="Psicotrópico",
                custom_control_level_change_reason=None
            )
        ])
        
        with self.assertRaises(frappe.ValidationError):
            self.validate_func(invoice)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("motivo", call_args[0][0].lower())
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.throw')
    def test_cambio_con_motivo_no_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Cambio en control level con motivo no debe lanzar error"""
        mock_exists.return_value = True
        
        mock_item_doc = Mock()
        mock_item_doc.get.return_value = "None"  # Control level actual
        mock_get_doc.return_value = mock_item_doc
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                custom_new_control_level="Psicotrópico",
                custom_control_level_change_reason="Corrección de clasificación"
            )
        ])
        
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.throw')
    def test_sin_cambio_no_valida(self, mock_throw, mock_exists, mock_get_doc):
        """Sin cambio en control level no debe validar"""
        mock_exists.return_value = True
        
        mock_item_doc = Mock()
        mock_item_doc.get.return_value = "Psicotrópico"  # Control level actual
        mock_get_doc.return_value = mock_item_doc
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                custom_new_control_level="Psicotrópico",  # Mismo valor
                custom_control_level_change_reason=None
            )
        ])
        
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.throw')
    def test_sin_nuevo_control_level_no_valida(self, mock_throw):
        """Sin nuevo control level especificado no debe validar"""
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                custom_new_control_level=None,
                custom_control_level_change_reason=None
            )
        ])
        
        self.validate_func(invoice)
        
        mock_throw.assert_not_called()


class TestDetectAndLogControlLevelChanges(unittest.TestCase):
    """
    Tests para detect_and_log_control_level_changes()
    
    Verifica que se detecten y registren correctamente los cambios
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.utils.domain.control_level_audit import detect_and_log_control_level_changes
        self.detect_func = detect_and_log_control_level_changes
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.log_control_level_change')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.commit')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.msgprint')
    def test_detecta_y_registra_cambio(self, mock_msgprint, mock_commit, mock_exists, mock_get_doc, mock_log):
        """Debe detectar y registrar cambio en control level"""
        mock_exists.return_value = True
        mock_log.return_value = "CLCL-001"
        
        mock_item_doc = Mock()
        mock_item_doc.get.return_value = "None"  # Control level actual
        mock_item_doc.custom_control_level = "None"
        mock_item_doc.save = Mock()
        mock_get_doc.return_value = mock_item_doc
        
        invoice = MockInvoice(
            items=[
                MockItem(
                    item_code="ITEM-001",
                    custom_new_control_level="Psicotrópico",
                    custom_control_level_change_reason="Corrección de clasificación"
                )
            ],
            name="SI-001"
        )
        
        self.detect_func(invoice)
        
        # Verificar que se llamó log_control_level_change
        mock_log.assert_called_once()
        call_args = mock_log.call_args
        self.assertEqual(call_args[1]["item_code"], "ITEM-001")
        self.assertEqual(call_args[1]["previous_control_level"], "None")
        self.assertEqual(call_args[1]["new_control_level"], "Psicotrópico")
        self.assertEqual(call_args[1]["reference_doctype"], "Sales Invoice")
        self.assertEqual(call_args[1]["reference_name"], "SI-001")
        
        # Verificar que se actualizó el Item
        self.assertEqual(mock_item_doc.custom_control_level, "Psicotrópico")
        mock_item_doc.save.assert_called_once_with(ignore_permissions=True)
        mock_commit.assert_called()
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.log_control_level_change')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.throw')
    def test_cambio_sin_motivo_lanza_error(self, mock_throw, mock_exists, mock_get_doc, mock_log):
        """Cambio sin motivo debe lanzar error"""
        mock_exists.return_value = True
        mock_throw.side_effect = frappe.ValidationError("Motivo requerido")
        
        mock_item_doc = Mock()
        mock_item_doc.get.return_value = "None"
        mock_get_doc.return_value = mock_item_doc
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                custom_new_control_level="Psicotrópico",
                custom_control_level_change_reason=None
            )
        ])
        
        with self.assertRaises(frappe.ValidationError):
            self.detect_func(invoice)
        
        mock_throw.assert_called_once()
        mock_log.assert_not_called()
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.log_control_level_change')
    def test_sin_cambio_no_registra(self, mock_log):
        """Sin cambio en control level no debe registrar"""
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                custom_new_control_level=None,
                custom_control_level_change_reason=None
            )
        ])
        
        self.detect_func(invoice)
        
        mock_log.assert_not_called()
    
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.log_control_level_change')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.get_doc')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.exists')
    @patch('barriofarma_app.barriofarma_app.utils.domain.control_level_audit.frappe.db.commit')
    def test_multiples_items_con_cambios(self, mock_commit, mock_exists, mock_get_doc, mock_log):
        """Múltiples items con cambios deben registrarse todos"""
        mock_exists.return_value = True
        mock_log.return_value = "CLCL-001"
        
        def get_doc_side_effect(doctype, name):
            if doctype == "Item":
                mock_item = Mock()
                mock_item.get.return_value = "None"
                mock_item.custom_control_level = "None"
                mock_item.save = Mock()
                return mock_item
            return Mock()
        
        mock_get_doc.side_effect = get_doc_side_effect
        
        invoice = MockInvoice(items=[
            MockItem(
                item_code="ITEM-001",
                custom_new_control_level="Psicotrópico",
                custom_control_level_change_reason="Corrección 1"
            ),
            MockItem(
                item_code="ITEM-002",
                custom_new_control_level="Estupefaciente",
                custom_control_level_change_reason="Corrección 2"
            )
        ])
        
        self.detect_func(invoice)
        
        # Verificar que se llamó log_control_level_change dos veces
        self.assertEqual(mock_log.call_count, 2)


class TestControlLevelChangeLogDocType(unittest.TestCase):
    """
    Tests para el DocType Control Level Change Log
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.doctype.control_level_change_log.control_level_change_log import ControlLevelChangeLog
        self.LogClass = ControlLevelChangeLog
    
    @patch('barriofarma_app.barriofarma_app.doctype.control_level_change_log.control_level_change_log.frappe.throw')
    def test_validate_sin_motivo_lanza_error(self, mock_throw):
        """Validación sin motivo debe lanzar error"""
        mock_throw.side_effect = frappe.ValidationError("Motivo requerido")
        
        log_doc = Mock()
        log_doc.reason = None
        log_doc.item_code = "ITEM-001"
        
        with patch('barriofarma_app.barriofarma_app.doctype.control_level_change_log.control_level_change_log.frappe.db.exists', return_value=True):
            with self.assertRaises(frappe.ValidationError):
                self.LogClass.validate(log_doc)
        
        mock_throw.assert_called_once()
    
    @patch('barriofarma_app.barriofarma_app.doctype.control_level_change_log.control_level_change_log.frappe.throw')
    def test_validate_sin_item_code_lanza_error(self, mock_throw):
        """Validación sin item_code debe lanzar error"""
        mock_throw.side_effect = frappe.ValidationError("Item requerido")
        
        log_doc = Mock()
        log_doc.reason = "Motivo válido"
        log_doc.item_code = None
        
        with self.assertRaises(frappe.ValidationError):
            self.LogClass.validate(log_doc)
        
        mock_throw.assert_called_once()
    
    @patch('barriofarma_app.barriofarma_app.doctype.control_level_change_log.control_level_change_log.frappe.db.exists')
    def test_validate_item_no_existe_lanza_error(self, mock_exists):
        """Validación con item que no existe debe lanzar error"""
        mock_exists.return_value = False
        
        log_doc = Mock()
        log_doc.reason = "Motivo válido"
        log_doc.item_code = "ITEM-NONEXISTENT"
        
        with self.assertRaises(frappe.ValidationError):
            self.LogClass.validate(log_doc)


if __name__ == '__main__':
    unittest.main()

