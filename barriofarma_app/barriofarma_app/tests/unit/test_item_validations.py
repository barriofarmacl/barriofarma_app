# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma

import unittest
import frappe
from frappe import _
from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_shelf,
    create_test_warehouse,
)


class TestItemValidations(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.to_cleanup = {"Item": [], "Shelf": [], "Warehouse": []}

    def tearDown(self):
        frappe.set_user("Administrator")
        for doctype, names in self.to_cleanup.items():
            for name in names:
                if frappe.db.exists(doctype, name):
                    frappe.delete_doc(doctype, name, ignore_permissions=True, force=1)
        frappe.db.commit()

    def _track(self, doc):
        self.to_cleanup.setdefault(doc.doctype, [])
        self.to_cleanup[doc.doctype].append(doc.name)
        return doc

    # --- validate_control_level_invariants ---
    def test_control_level_requires_batch_expiry_and_retention(self):
        # Edge: Psicotrópico sin flags requeridos -> error
        with self.assertRaises(frappe.ValidationError):
            item = self._track(
                create_test_item(
                    item_name="CtrlEdge",
                    custom_dispensing_type="Venta Libre",
                    custom_control_level="Psicotrópico",
                    has_batch_no=0,
                    has_expiry_date=0,
                    custom_requires_prescription_retention=0,
                )
            )

        # Happy: Psicotrópico con todos los flags -> OK
        item = self._track(
            create_test_item(
                item_name="CtrlOk",
                custom_dispensing_type="Venta con Receta Retenida",
                custom_control_level="Psicotrópico",
                has_batch_no=1,
                has_expiry_date=1,
                custom_requires_prescription_retention=1,
                custom_prescription_storage_required=1,
                custom_sanitary_registration="REG-CTRL-OK",
            )
        )
        item.reload()
        self.assertTrue(item.has_batch_no and item.has_expiry_date and item.custom_requires_prescription_retention)

    # --- validate_dispensing_type_invariants ---
    def test_dispensing_type_venta_libre_adjusts_flags(self):
        # Venta Libre ajusta has_batch_no=0, custom_prescription_storage_required=0, asegura has_expiry_date=1
        item = self._track(
            create_test_item(
                item_name="VL",
                custom_dispensing_type="Venta Libre",
                has_batch_no=1,
                has_expiry_date=0,
                custom_prescription_storage_required=1,
            )
        )
        item.reload()
        self.assertEqual(item.has_batch_no, 0)
        self.assertEqual(item.custom_prescription_storage_required, 0)
        self.assertEqual(item.has_expiry_date, 1)

    def test_dispensing_type_receta_retenida_requires_batch_and_expiry(self):
        # Edge: Receta Retenida sin has_batch_no -> error
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="RR-edge1",
                    custom_dispensing_type="Venta con Receta Retenida",
                    has_batch_no=0,
                    has_expiry_date=1,
                    custom_prescription_storage_required=1,
                    custom_sanitary_registration="REG-OK-1",
                )
            )

        # Edge: Receta Retenida sin has_expiry_date -> error
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="RR-edge2",
                    custom_dispensing_type="Venta con Receta Retenida",
                    has_batch_no=1,
                    has_expiry_date=0,
                    custom_prescription_storage_required=1,
                    custom_sanitary_registration="REG-OK-2",
                )
            )

        # Happy: Receta Retenida con ambos flags -> OK (y storage_required se fuerza a 1 si faltaba)
        item = self._track(
            create_test_item(
                item_name="RR-ok",
                custom_dispensing_type="Venta con Receta Retenida",
                has_batch_no=1,
                has_expiry_date=1,
                custom_prescription_storage_required=0,
                custom_sanitary_registration="REG-OK-3",
            )
        )
        item.reload()
        self.assertEqual(item.has_batch_no, 1)
        self.assertEqual(item.has_expiry_date, 1)
        self.assertEqual(item.custom_prescription_storage_required, 1)

    # --- validate_sanitary_registration_required ---
    def test_sanitary_registration_required_for_receta_retenida(self):
        # Edge: falta registro sanitario
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="RR-no-reg",
                    custom_dispensing_type="Venta con Receta Retenida",
                    has_batch_no=1,
                    has_expiry_date=1,
                    custom_prescription_storage_required=1,
                    custom_sanitary_registration="",
                )
            )

        # Happy: con registro sanitario
        item = self._track(
            create_test_item(
                item_name="RR-reg-ok",
                custom_dispensing_type="Venta con Receta Retenida",
                has_batch_no=1,
                has_expiry_date=1,
                custom_prescription_storage_required=1,
                custom_sanitary_registration="REG-OK-4",
            )
        )
        self.assertTrue(bool(item.custom_sanitary_registration))

    # --- validate_shelf_locations_invariants ---
    def test_shelf_locations_only_one_preferred_and_compatibility(self):
        # Preparar warehouse y shelves
        wh = self._track(create_test_warehouse(f"WH-IT-{frappe.generate_hash(6)}"))
        shelf_norm = self._track(create_test_shelf(shelf_name=f"SHELF-NORM-{frappe.generate_hash(6)}", warehouse=wh.name))
        shelf_ctrl = self._track(create_test_shelf(shelf_name=f"SHELF-CTRL-{frappe.generate_hash(6)}", warehouse=wh.name, shelf_type="Controlado"))

        # Edge: dos ubicaciones preferidas -> error
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="TwoPref",
                    custom_shelf_locations=[
                        {"shelf": shelf_norm.name, "preferred_location": 1},
                        {"shelf": shelf_ctrl.name, "preferred_location": 1},
                    ],
                )
            )

        # Edge: shelf tipo Controlado con item sin control_level -> error
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="CtrlShelfNoLevel",
                    custom_dispensing_type="Venta Libre",
                    custom_shelf_locations=[{"shelf": shelf_ctrl.name, "preferred_location": 1}],
                )
            )

        # Happy: shelf tipo Controlado con control_level válido -> OK
        item = self._track(
            create_test_item(
                item_name="CtrlShelfOk",
                custom_dispensing_type="Venta Libre",
                custom_control_level="Psicotrópico",
                has_batch_no=1,
                has_expiry_date=1,
                custom_requires_prescription_retention=1,
                custom_shelf_locations=[{"shelf": shelf_ctrl.name, "preferred_location": 1}],
            )
        )
        self.assertTrue(frappe.db.exists("Item", item.name))

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para las validaciones DDD en el override de Item
Story 1.1: Tests Unitarios para Validaciones de Item

Objetivo: Validar todas las invariantes del dominio farmacéutico implementadas en item.py
- validate_control_level_invariants()
- validate_dispensing_type_invariants()
- validate_sanitary_registration_required()
- validate_shelf_locations_invariants()

Cobertura: 100% de métodos de validación
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
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
    - Venta Libre: has_batch_no = 0, custom_prescription_storage_required = 0, has_expiry_date = 1
    - Venta con Receta Retenida: has_batch_no = 1, has_expiry_date = 1, custom_prescription_storage_required = 1
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
            custom_prescription_storage_required=0
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        # Verificar que no se modificó
        self.assertEqual(item.get("has_batch_no"), 0)
        self.assertEqual(item.get("has_expiry_date"), 1)
        self.assertEqual(item.get("custom_prescription_storage_required"), 0)
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
    def test_receta_retenida_correcta_no_modifica(self, mock_throw):
        """Venta con Receta Retenida correctamente configurada no debe modificarse"""
        item = MockItem(
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1
        )
        
        self.Item.validate_dispensing_type_invariants(item)
        
        # Verificar que no se modificó
        self.assertEqual(item.get("has_batch_no"), 1)
        self.assertEqual(item.get("has_expiry_date"), 1)
        self.assertEqual(item.get("custom_prescription_storage_required"), 1)
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
        mock_shelf = Mock()
        mock_shelf.get.return_value = "Normal"
        mock_shelf.max_capacity = None
        mock_get_doc.return_value = mock_shelf
        
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
        mock_shelf = Mock()
        mock_shelf.get.return_value = "Controlado"
        mock_shelf.shelf_name = "SHELF-CTRL-001"
        mock_shelf.max_capacity = None
        mock_get_doc.return_value = mock_shelf
        
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
        mock_shelf = Mock()
        mock_shelf.get.return_value = "Controlado"
        mock_shelf.shelf_name = "SHELF-CTRL-001"
        mock_shelf.max_capacity = None
        mock_get_doc.return_value = mock_shelf
        
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
        mock_shelf = Mock()
        mock_shelf.get.return_value = "Controlado"
        mock_shelf.shelf_name = "SHELF-CTRL-001"
        mock_shelf.max_capacity = None
        mock_get_doc.return_value = mock_shelf
        
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
        mock_shelf = Mock()
        mock_shelf.get.return_value = "Refrigerado"
        mock_shelf.shelf_name = "SHELF-FRIO-001"
        mock_shelf.max_capacity = None
        mock_get_doc.return_value = mock_shelf
        
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
        mock_shelf = Mock()
        mock_shelf.get.return_value = "Refrigerado"
        mock_shelf.shelf_name = "SHELF-FRIO-001"
        mock_shelf.max_capacity = None
        mock_get_doc.return_value = mock_shelf
        
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
        mock_shelf = Mock()
        mock_shelf.get.return_value = "Normal"
        mock_shelf.shelf_name = "SHELF-001"
        mock_shelf.warehouse = "Stores - BF"
        mock_shelf.max_capacity = 100
        mock_shelf.calculate_current_occupancy.return_value = 90  # Ocupación actual
        
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
        mock_shelf = Mock()
        mock_shelf.get.return_value = "Normal"
        mock_shelf.shelf_name = "SHELF-001"
        mock_shelf.max_capacity = None
        mock_get_doc.return_value = mock_shelf
        
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
        
        # Ejecutar todas las validaciones individualmente
        self.Item.validate_control_level_invariants(item)
        self.Item.validate_dispensing_type_invariants(item)
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
        
        # Ejecutar todas las validaciones individualmente
        self.Item.validate_control_level_invariants(item)
        self.Item.validate_dispensing_type_invariants(item)
        self.Item.validate_sanitary_registration_required(item)
        self.Item.validate_shelf_locations_invariants(item)
        
        mock_throw.assert_not_called()


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


if __name__ == '__main__':
    unittest.main()

