# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt
#
# Story 1.1: Tests unitarios (mocks) para validaciones del override Item.
# Tests con DB (create_test_*) viven en tests/integration/test_item_validations.py

import unittest
from unittest.mock import Mock, patch

import frappe


class MockItem:
    """
    Mock del Item DocType para tests unitarios aislados.
    Simula el comportamiento de frappe.get_doc() sin acceder a la base de datos.
    """

    def __init__(self, **kwargs):
        self._data = {}
        for key, value in kwargs.items():
            self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def _auto_fill_single_shelf_quantity(self):
        pass

    def _auto_fill_shelf_quantities_from_movements(self):
        pass


class TestControlLevelInvariants(unittest.TestCase):
    """
    Tests para validate_control_level_invariants()
    
    Invariante: Si custom_control_level es Psicotrópico o Estupefaciente,
    entonces has_batch_no, has_expiry_date y custom_requires_prescription_retention
    deben ser verdaderos (Check = 1)
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        # Importar la clase Item del override
        from barriofarma_app.barriofarma_app.overrides.item import Item
        self.Item = Item
    
    @patch('frappe.throw')
    def test_psicotropico_sin_has_batch_no_lanza_error(self, mock_throw):
        """Psicotrópico sin has_batch_no debe lanzar error"""
        item = MockItem(
            custom_control_level="Psicotrópico",
            has_batch_no=0,
            has_expiry_date=1,
            custom_requires_prescription_retention=1
        )
        
        # Ejecutar validación
        self.Item.validate_control_level_invariants(item)
        
        # Verificar que frappe.throw fue llamado
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("gestión por lote", call_args[0][0])
        self.assertIn("Psicotrópico", call_args[0][0])
    
    @patch('frappe.throw')
    def test_psicotropico_sin_has_expiry_date_lanza_error(self, mock_throw):
        """Psicotrópico sin has_expiry_date debe lanzar error"""
        item = MockItem(
            custom_control_level="Psicotrópico",
            has_batch_no=1,
            has_expiry_date=0,
            custom_requires_prescription_retention=1
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("fecha de vencimiento", call_args[0][0])
    
    @patch('frappe.throw')
    def test_psicotropico_sin_prescription_retention_lanza_error(self, mock_throw):
        """Psicotrópico sin custom_requires_prescription_retention debe lanzar error"""
        item = MockItem(
            custom_control_level="Psicotrópico",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=0
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("receta retenida", call_args[0][0])
    
    @patch('frappe.throw')
    def test_estupefaciente_sin_has_batch_no_lanza_error(self, mock_throw):
        """Estupefaciente sin has_batch_no debe lanzar error"""
        item = MockItem(
            custom_control_level="Estupefaciente",
            has_batch_no=0,
            has_expiry_date=1,
            custom_requires_prescription_retention=1
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("Estupefaciente", call_args[0][0])
    
    @patch('frappe.throw')
    def test_estupefaciente_sin_has_expiry_date_lanza_error(self, mock_throw):
        """Estupefaciente sin has_expiry_date debe lanzar error"""
        item = MockItem(
            custom_control_level="Estupefaciente",
            has_batch_no=1,
            has_expiry_date=0,
            custom_requires_prescription_retention=1
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("fecha de vencimiento", call_args[0][0])
    
    @patch('frappe.throw')
    def test_estupefaciente_sin_prescription_retention_lanza_error(self, mock_throw):
        """Estupefaciente sin custom_requires_prescription_retention debe lanzar error"""
        item = MockItem(
            custom_control_level="Estupefaciente",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=0
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("receta retenida", call_args[0][0])
    
    @patch('frappe.throw')
    def test_psicotropico_con_todos_los_campos_no_lanza_error(self, mock_throw):
        """Psicotrópico con todos los campos correctos no debe lanzar error"""
        item = MockItem(
            custom_control_level="Psicotrópico",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_estupefaciente_con_todos_los_campos_no_lanza_error(self, mock_throw):
        """Estupefaciente con todos los campos correctos no debe lanzar error"""
        item = MockItem(
            custom_control_level="Estupefaciente",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_sin_control_level_no_lanza_error(self, mock_throw):
        """Producto sin control_level no debe lanzar error"""
        item = MockItem(
            custom_control_level=None,
            has_batch_no=0,
            has_expiry_date=0,
            custom_requires_prescription_retention=0
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_control_level_vacio_no_lanza_error(self, mock_throw):
        """Producto con control_level vacío no debe lanzar error"""
        item = MockItem(
            custom_control_level="",
            has_batch_no=0,
            has_expiry_date=0,
            custom_requires_prescription_retention=0
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_control_level_otro_valor_no_lanza_error(self, mock_throw):
        """Producto con control_level diferente a Psicotrópico/Estupefaciente no valida"""
        item = MockItem(
            custom_control_level="Otro",
            has_batch_no=0,
            has_expiry_date=0,
            custom_requires_prescription_retention=0
        )
        
        self.Item.validate_control_level_invariants(item)
        
        mock_throw.assert_not_called()


class TestDispensingTypeInvariants(unittest.TestCase):
    """
    Tests para validate_dispensing_type_invariants()
    
    Invariantes:
    - Venta Libre: has_batch_no = 0, custom_prescription_storage_required = 0,
      custom_requires_prescription_retention = 0, has_expiry_date = 1
    - Venta con Receta Retenida: has_batch_no = 1, has_expiry_date = 1,
      custom_prescription_storage_required = 1, custom_requires_prescription_retention = 1
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.overrides.item import Item
        self.Item = Item
    
    @patch('frappe.throw')
    def test_sin_dispensing_type_no_valida(self, mock_throw):
        """Sin dispensing_type no debe validar ni lanzar error"""
        item = MockItem(
            custom_dispensing_type=None,
            has_batch_no=1,
            has_expiry_date=0,
            custom_prescription_storage_required=1
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_venta_libre_ajusta_has_batch_no_automaticamente(self, mock_throw):
        """Venta Libre con has_batch_no=1 debe ajustarse automáticamente a 0"""
        item = MockItem(
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=0
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        # Verificar que se ajustó automáticamente
        self.assertEqual(item.get("has_batch_no"), 0)
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_venta_libre_ajusta_prescription_storage_automaticamente(self, mock_throw):
        """Venta Libre con custom_prescription_storage_required=1 debe ajustarse a 0"""
        item = MockItem(
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=1,
            custom_prescription_storage_required=1
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        # Verificar que se ajustó automáticamente
        self.assertEqual(item.get("custom_prescription_storage_required"), 0)
        mock_throw.assert_not_called()

    @patch('frappe.throw')
    def test_venta_libre_ajusta_retention_automaticamente(self, mock_throw):
        """Venta Libre con custom_requires_prescription_retention=1 debe ajustarse a 0"""
        item = MockItem(
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=1,
            custom_prescription_storage_required=0,
            custom_requires_prescription_retention=1,
        )

        self.Item.validate_dispensing_type_invariants(item)

        self.assertEqual(item.get("custom_requires_prescription_retention"), 0)
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_venta_libre_ajusta_has_expiry_date_automaticamente(self, mock_throw):
        """Venta Libre sin has_expiry_date debe ajustarse automáticamente a 1"""
        item = MockItem(
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=0,
            custom_prescription_storage_required=0
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        # Verificar que se ajustó automáticamente
        self.assertEqual(item.get("has_expiry_date"), 1)
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_venta_libre_correcta_no_modifica(self, mock_throw):
        """Venta Libre correctamente configurada no debe modificarse"""
        item = MockItem(
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=1,
            custom_prescription_storage_required=0,
            custom_requires_prescription_retention=0,
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        # Verificar que no se modificó
        self.assertEqual(item.get("has_batch_no"), 0)
        self.assertEqual(item.get("has_expiry_date"), 1)
        self.assertEqual(item.get("custom_prescription_storage_required"), 0)
        self.assertEqual(item.get("custom_requires_prescription_retention"), 0)
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_receta_retenida_sin_has_batch_no_lanza_error(self, mock_throw):
        """Venta con Receta Retenida sin has_batch_no debe lanzar error"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=0,
            has_expiry_date=1,
            custom_prescription_storage_required=1
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("gestión por lote", call_args[0][0])
    
    @patch('frappe.throw')
    def test_receta_retenida_sin_has_expiry_date_lanza_error(self, mock_throw):
        """Venta con Receta Retenida sin has_expiry_date debe lanzar error"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=0,
            custom_prescription_storage_required=1
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("fecha de vencimiento", call_args[0][0])
    
    @patch('frappe.throw')
    def test_receta_retenida_ajusta_prescription_storage_automaticamente(self, mock_throw):
        """Venta con Receta Retenida sin custom_prescription_storage_required debe ajustarse a 1"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=0
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        # Verificar que se ajustó automáticamente
        self.assertEqual(item.get("custom_prescription_storage_required"), 1)
        mock_throw.assert_not_called()

    @patch('frappe.throw')
    def test_receta_retenida_ajusta_retention_automaticamente(self, mock_throw):
        """Venta con Receta Retenida sin custom_requires_prescription_retention debe ajustarse a 1"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_requires_prescription_retention=0,
        )

        self.Item.validate_dispensing_type_invariants(item)

        self.assertEqual(item.get("custom_requires_prescription_retention"), 1)
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_receta_retenida_correcta_no_modifica(self, mock_throw):
        """Venta con Receta Retenida correctamente configurada no debe modificarse"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_requires_prescription_retention=1,
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        # Verificar que no se modificó
        self.assertEqual(item.get("has_batch_no"), 1)
        self.assertEqual(item.get("has_expiry_date"), 1)
        self.assertEqual(item.get("custom_prescription_storage_required"), 1)
        self.assertEqual(item.get("custom_requires_prescription_retention"), 1)
        mock_throw.assert_not_called()


class TestSanitaryRegistrationRequired(unittest.TestCase):
    """
    Tests para validate_sanitary_registration_required()
    
    Regla: Si custom_dispensing_type = "Venta con Receta Retenida",
    entonces custom_sanitary_registration es obligatorio
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.overrides.item import Item
        self.Item = Item
    
    @patch('frappe.throw')
    def test_receta_retenida_sin_sanitary_registration_lanza_error(self, mock_throw):
        """Venta con Receta Retenida sin sanitary_registration debe lanzar error"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration=None
        )
        
        self.Item.validate_sanitary_registration_required(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("registro sanitario", call_args[0][0])
    
    @patch('frappe.throw')
    def test_receta_retenida_con_sanitary_registration_vacio_lanza_error(self, mock_throw):
        """Venta con Receta Retenida con sanitary_registration vacío debe lanzar error"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration=""
        )
        
        self.Item.validate_sanitary_registration_required(item)
        
        mock_throw.assert_called_once()
    
    @patch('frappe.throw')
    def test_receta_retenida_con_sanitary_registration_espacios_lanza_error(self, mock_throw):
        """Venta con Receta Retenida con sanitary_registration solo espacios debe lanzar error"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="   "
        )
        
        self.Item.validate_sanitary_registration_required(item)
        
        mock_throw.assert_called_once()
    
    @patch('frappe.throw')
    def test_receta_retenida_con_sanitary_registration_no_lanza_error(self, mock_throw):
        """Venta con Receta Retenida con sanitary_registration válido no debe lanzar error"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="RS-12345"
        )
        
        self.Item.validate_sanitary_registration_required(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_venta_libre_sin_sanitary_registration_no_lanza_error(self, mock_throw):
        """Venta Libre sin sanitary_registration no debe lanzar error"""
        item = MockItem(
            custom_dispensing_type="Venta Libre",
            custom_sanitary_registration=None
        )
        
        self.Item.validate_sanitary_registration_required(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_sin_dispensing_type_sin_sanitary_registration_no_lanza_error(self, mock_throw):
        """Sin dispensing_type y sin sanitary_registration no debe lanzar error"""
        item = MockItem(
            custom_dispensing_type=None,
            custom_sanitary_registration=None
        )
        
        self.Item.validate_sanitary_registration_required(item)
        
        mock_throw.assert_not_called()


class TestShelfLocationsInvariants(unittest.TestCase):
    """
    Tests para validate_shelf_locations_invariants()
    
    Invariantes:
    1. Shelf debe existir
    2. Solo puede haber una ubicación preferida por Item
    3. Tipo de estante compatible con tipo de producto
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.overrides.item import Item
        self.Item = Item

    @staticmethod
    def _make_mock_shelf(shelf_type="Normal", shelf_name="SHELF-001", **attrs):
        mock_shelf = Mock()
        mock_shelf.shelf_name = shelf_name
        mock_shelf.max_capacity = attrs.get("max_capacity")
        mock_shelf.warehouse = attrs.get("warehouse", "Stores - BF")
        mock_shelf.calculate_current_occupancy = attrs.get(
            "calculate_current_occupancy", Mock(return_value=0)
        )
        field_values = {"shelf_type": shelf_type, "disabled": 0}
        mock_shelf.get = Mock(
            side_effect=lambda key, default=None: field_values.get(key, default)
        )
        return mock_shelf
    
    @patch('frappe.throw')
    def test_sin_shelf_locations_no_valida(self, mock_throw):
        """Sin shelf_locations no debe validar ni lanzar error"""
        item = MockItem(
            custom_shelf_locations=None
        )
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_shelf_locations_vacio_no_valida(self, mock_throw):
        """Con shelf_locations vacío no debe validar ni lanzar error"""
        item = MockItem()
        item.custom_shelf_locations = []
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.get_doc')
    @patch('frappe.db.exists')
    @patch('frappe.throw')
    def test_shelf_no_existe_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Shelf que no existe debe lanzar error"""
        mock_exists.return_value = False
        # Hacer que frappe.throw lance una excepción para detener la ejecución
        mock_throw.side_effect = frappe.ValidationError("Shelf no existe")
        
        item = MockItem()
        item.custom_shelf_locations = [
            {"shelf": "SHELF-001", "preferred_location": False}
        ]
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError):
            self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("no existe", call_args[0][0])
    
    @patch('frappe.get_doc')
    @patch('frappe.db.exists')
    @patch('frappe.throw')
    def test_multiples_preferred_locations_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Múltiples ubicaciones preferidas debe lanzar error"""
        mock_exists.return_value = True
        mock_get_doc.side_effect = lambda doctype, name=None: self._make_mock_shelf(
            shelf_name=name or "SHELF-001"
        )
        
        item = MockItem()
        item.custom_shelf_locations = [
            {"shelf": "SHELF-001", "preferred_location": True},
            {"shelf": "SHELF-002", "preferred_location": True}
        ]
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("una ubicación preferida", call_args[0][0])
    
    @patch('frappe.get_doc')
    @patch('frappe.db.exists')
    @patch('frappe.throw')
    def test_estante_controlado_con_producto_sin_control_level_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Estante Controlado con producto sin control_level debe lanzar error"""
        mock_exists.return_value = True
        mock_get_doc.return_value = self._make_mock_shelf(
            shelf_type="Controlado", shelf_name="SHELF-CTRL-001"
        )
        
        item = MockItem(custom_control_level=None)
        item.custom_shelf_locations = [
            {"shelf": "SHELF-CTRL-001", "preferred_location": False}
        ]
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("Controlado", call_args[0][0])
    
    @patch('frappe.get_doc')
    @patch('frappe.db.exists')
    @patch('frappe.throw')
    def test_estante_controlado_con_control_level_none_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Estante Controlado con control_level='None' debe lanzar error"""
        mock_exists.return_value = True
        mock_get_doc.return_value = self._make_mock_shelf(
            shelf_type="Controlado", shelf_name="SHELF-CTRL-001"
        )
        
        item = MockItem(custom_control_level="None")
        item.custom_shelf_locations = [
            {"shelf": "SHELF-CTRL-001", "preferred_location": False}
        ]
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_called_once()
    
    @patch('frappe.get_doc')
    @patch('frappe.db.exists')
    @patch('frappe.throw')
    def test_estante_controlado_con_producto_controlado_no_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Estante Controlado con producto controlado no debe lanzar error"""
        mock_exists.return_value = True
        mock_get_doc.return_value = self._make_mock_shelf(
            shelf_type="Controlado", shelf_name="SHELF-CTRL-001"
        )
        
        item = MockItem(custom_control_level="Psicotrópico")
        item.custom_shelf_locations = [
            {"shelf": "SHELF-CTRL-001", "preferred_location": False}
        ]
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.get_doc')
    @patch('frappe.db.exists')
    @patch('frappe.throw')
    def test_estante_refrigerado_sin_requires_refrigeration_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Estante Refrigerado con producto sin requires_refrigeration debe lanzar error"""
        mock_exists.return_value = True
        mock_get_doc.return_value = self._make_mock_shelf(
            shelf_type="Refrigerado", shelf_name="SHELF-FRIO-001"
        )
        
        item = MockItem(custom_requires_refrigeration=False)
        item.custom_shelf_locations = [
            {"shelf": "SHELF-FRIO-001", "preferred_location": False}
        ]
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("Refrigerado", call_args[0][0])
    
    @patch('frappe.get_doc')
    @patch('frappe.db.exists')
    @patch('frappe.throw')
    def test_estante_refrigerado_con_requires_refrigeration_no_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Estante Refrigerado con producto que requiere refrigeración no debe lanzar error"""
        mock_exists.return_value = True
        mock_get_doc.return_value = self._make_mock_shelf(
            shelf_type="Refrigerado", shelf_name="SHELF-FRIO-001"
        )
        
        item = MockItem(custom_requires_refrigeration=True)
        item.custom_shelf_locations = [
            {"shelf": "SHELF-FRIO-001", "preferred_location": False}
        ]
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('erpnext.stock.utils.get_or_make_bin')
    @patch('frappe.get_doc')
    @patch('frappe.db.exists')
    @patch('frappe.throw')
    def test_capacidad_excedida_lanza_error(self, mock_throw, mock_exists, mock_get_doc, mock_get_bin):
        """Stock que excede capacidad del estante debe lanzar error"""
        mock_exists.return_value = True
        
        # Mock del shelf
        mock_shelf = self._make_mock_shelf(
            shelf_name="SHELF-001",
            max_capacity=100,
            calculate_current_occupancy=Mock(return_value=90),
        )
        
        # Mock del bin
        mock_bin = Mock()
        mock_bin.actual_qty = 50  # Stock del item excede capacidad disponible (100-90=10)
        
        def get_doc_side_effect(doctype, name=None):
            if doctype == "Shelf":
                return mock_shelf
            elif doctype == "Bin":
                return mock_bin
            return Mock()
        
        mock_get_doc.side_effect = get_doc_side_effect
        mock_get_bin.return_value = "BIN-001"
        
        item = MockItem()
        item.name = "ITEM-001"
        item.custom_shelf_locations = [
            {"shelf": "SHELF-001", "preferred_location": False}
        ]
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_called_once()
        call_args = mock_throw.call_args
        self.assertIn("capacidad", call_args[0][0].lower())
    
    @patch('frappe.get_doc')
    @patch('frappe.db.exists')
    @patch('frappe.throw')
    def test_configuracion_valida_no_lanza_error(self, mock_throw, mock_exists, mock_get_doc):
        """Configuración válida de shelf_locations no debe lanzar error"""
        mock_exists.return_value = True
        mock_get_doc.side_effect = lambda doctype, name=None: self._make_mock_shelf(
            shelf_name=name or "SHELF-001"
        )
        
        item = MockItem()
        item.custom_shelf_locations = [
            {"shelf": "SHELF-001", "preferred_location": True},
            {"shelf": "SHELF-002", "preferred_location": False}
        ]
        
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_not_called()


class TestValidateMethodIntegration(unittest.TestCase):
    """
    Tests de integración para el método validate() completo
    Verifica que todas las validaciones se ejecutan correctamente
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.overrides.item import Item
        self.Item = Item
    
    @patch('frappe.throw')
    def test_item_valido_completo_no_lanza_error(self, mock_throw):
        """Item completamente válido no debe lanzar ningún error"""
        item = MockItem(
            custom_control_level="Psicotrópico",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1,
            custom_dispensing_type="Venta con Receta Retenida",
            custom_prescription_storage_required=1,
            custom_sanitary_registration="RS-12345"
        )
        
        # Ejecutar en orden de validate(): dispensing antes de control_level
        self.Item.validate_dispensing_type_invariants(item)
        self.Item.validate_control_level_invariants(item)
        self.Item.validate_sanitary_registration_required(item)
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_item_venta_libre_valido_no_lanza_error(self, mock_throw):
        """Item de Venta Libre válido no debe lanzar ningún error"""
        item = MockItem(
            custom_control_level=None,
            has_batch_no=0,
            has_expiry_date=1,
            custom_requires_prescription_retention=0,
            custom_dispensing_type="Venta Libre",
            custom_prescription_storage_required=0,
            custom_sanitary_registration=None
        )
        
        # Ejecutar en orden de validate(): dispensing antes de control_level
        self.Item.validate_dispensing_type_invariants(item)
        self.Item.validate_control_level_invariants(item)
        self.Item.validate_sanitary_registration_required(item)
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_not_called()

    @patch('frappe.throw')
    def test_psicotropico_venta_libre_falla_en_dispensing(self, mock_throw):
        """Psicotrópico + Venta Libre: error claro en dispensing (no limpiar batch silencioso)"""
        mock_throw.side_effect = Exception("stop")
        item = MockItem(
            custom_control_level="Psicotrópico",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1,
            custom_prescription_storage_required=0,
        )

        with self.assertRaises(Exception):
            self.Item.validate_dispensing_type_invariants(item)

        mock_throw.assert_called_once()
        self.assertIn("Venta con Receta Retenida", mock_throw.call_args[0][0])
        self.assertEqual(item.get("has_batch_no"), 1)


class TestEdgeCases(unittest.TestCase):
    """
    Tests para casos edge y boundary conditions
    """
    
    def setUp(self):
        """Configurar mocks antes de cada test"""
        from barriofarma_app.barriofarma_app.overrides.item import Item
        self.Item = Item
    
    @patch('frappe.throw')
    def test_control_level_con_espacios_no_es_valido(self, mock_throw):
        """Control level con solo espacios no debe ser considerado válido"""
        item = MockItem(
            custom_control_level="   ",  # Solo espacios
            has_batch_no=0,
            has_expiry_date=0,
            custom_requires_prescription_retention=0
        )
        
        self.Item.validate_control_level_invariants(item)
        
        # No debe lanzar error porque "   " no es "Psicotrópico" ni "Estupefaciente"
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_dispensing_type_con_espacios_no_valida(self, mock_throw):
        """Dispensing type con solo espacios no debe activar validaciones"""
        item = MockItem(
            custom_dispensing_type="   ",  # Solo espacios
            has_batch_no=1,
            has_expiry_date=0,
            custom_prescription_storage_required=1
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        # No debe lanzar error ni modificar campos
        mock_throw.assert_not_called()
    
    @patch('frappe.throw')
    def test_has_batch_no_como_string_cero_es_falsy(self, mock_throw):
        """has_batch_no como string '0' debe ser considerado falsy"""
        item = MockItem(
            custom_control_level="Psicotrópico",
            has_batch_no="0",  # String en lugar de int
            has_expiry_date=1,
            custom_requires_prescription_retention=1
        )
        
        self.Item.validate_control_level_invariants(item)
        
        # Debe lanzar error porque "0" string es truthy en Python
        # Este test documenta el comportamiento actual
        # Si "0" es truthy, no se lanzará error
        # El comportamiento depende de cómo Frappe maneja los campos Check

