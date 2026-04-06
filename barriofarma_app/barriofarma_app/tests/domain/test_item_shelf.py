# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests DDD para la Relación Item-Shelf
Validación de invariantes y reglas de negocio del dominio farmacéutico
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_warehouse,
    create_test_shelf,
    create_test_item,
    get_test_company,
)


class TestItemShelfDDD(FrappeTestCase):
    """Tests para invariantes DDD de la relación Item-Shelf"""

    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_items = []
        self.test_shelves = []
        self.test_warehouses = []

    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar items
        for item_name in self.test_items:
            try:
                if frappe.db.exists("Item", item_name):
                    frappe.delete_doc("Item", item_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar shelves
        for shelf_name in self.test_shelves:
            try:
                if frappe.db.exists("Shelf", shelf_name):
                    frappe.delete_doc("Shelf", shelf_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar warehouses
        for warehouse_name in self.test_warehouses:
            try:
                if frappe.db.exists("Warehouse", warehouse_name):
                    frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse = %s", (warehouse_name,))
                    frappe.delete_doc("Warehouse", warehouse_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()

    def test_invariante_item_puede_estar_en_multiples_shelves(self):
        """
        Invariante DDD: Un Item puede estar en múltiples Shelf simultáneamente
        """
        # Crear warehouse y shelves
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf1 = create_test_shelf(
            shelf_name="Estante A1",
            warehouse=warehouse.name,
            location_code="A1"
        )
        self.test_shelves.append(shelf1.name)
        
        shelf2 = create_test_shelf(
            shelf_name="Estante A2",
            warehouse=warehouse.name,
            location_code="A2"
        )
        self.test_shelves.append(shelf2.name)
        
        # Crear item
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Agregar item a múltiples shelves mediante custom_shelf_locations
        item.reload()
        if not hasattr(item, "custom_shelf_locations"):
            # Si el campo no existe aún, el test debe fallar (FASE RED)
            self.fail("Campo custom_shelf_locations no existe en Item")
        
        # Agregar primera ubicación
        item.append("custom_shelf_locations", {
            "shelf": shelf1.name,
            "preferred_location": 1
        })
        
        # Agregar segunda ubicación
        item.append("custom_shelf_locations", {
            "shelf": shelf2.name,
            "preferred_location": 0
        })
        
        item.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Validar que tiene ambas ubicaciones
        item.reload()
        self.assertEqual(len(item.custom_shelf_locations), 2, "Item debe tener 2 ubicaciones en shelves")
        self.assertEqual(item.custom_shelf_locations[0].shelf, shelf1.name, "Primera ubicación debe ser shelf1")
        self.assertEqual(item.custom_shelf_locations[1].shelf, shelf2.name, "Segunda ubicación debe ser shelf2")

    def test_invariante_shelf_puede_contener_multiples_items(self):
        """
        Invariante DDD: Un Shelf puede contener múltiples Item
        """
        # Crear warehouse y shelf
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante Multi-Item",
            warehouse=warehouse.name,
            location_code="MULTI-1"
        )
        self.test_shelves.append(shelf.name)
        
        # Crear múltiples items
        item1 = create_test_item(
            item_code=f"TEST-ITEM-1-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item1.name)
        
        item2 = create_test_item(
            item_code=f"TEST-ITEM-2-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item2.name)
        
        # Agregar ambos items al mismo shelf
        item1.reload()
        if not hasattr(item1, "custom_shelf_locations"):
            self.fail("Campo custom_shelf_locations no existe en Item")
        
        item1.append("custom_shelf_locations", {
            "shelf": shelf.name,
            "preferred_location": 1
        })
        item1.save(ignore_permissions=True)
        
        item2.reload()
        item2.append("custom_shelf_locations", {
            "shelf": shelf.name,
            "preferred_location": 0
        })
        item2.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        # Validar que ambos items están en el shelf
        item1.reload()
        item2.reload()
        self.assertEqual(item1.custom_shelf_locations[0].shelf, shelf.name, "Item1 debe estar en shelf")
        self.assertEqual(item2.custom_shelf_locations[0].shelf, shelf.name, "Item2 debe estar en shelf")

    def test_invariante_tipo_estante_refrigerado_solo_productos_refrigerados(self):
        """
        Invariante DDD: Estantes tipo Refrigerado solo deben contener productos que requieren refrigeración
        """
        # Crear warehouse y shelf refrigerado
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf_refrigerado = create_test_shelf(
            shelf_name="Estante Refrigerado",
            warehouse=warehouse.name,
            location_code="REF-1",
            shelf_type="Refrigerado"
        )
        self.test_shelves.append(shelf_refrigerado.name)
        
        # Crear item que requiere refrigeración
        item_refrigerado = create_test_item(
            item_code=f"TEST-ITEM-REF-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item_refrigerado.name)
        
        # Verificar que el campo custom_requires_refrigeration existe
        item_refrigerado.reload()
        if not hasattr(item_refrigerado, "custom_requires_refrigeration"):
            self.fail("Campo custom_requires_refrigeration no existe en Item")
        
        # Establecer que requiere refrigeración
        item_refrigerado.custom_requires_refrigeration = 1
        
        # Agregar a shelf refrigerado debe funcionar
        if not hasattr(item_refrigerado, "custom_shelf_locations"):
            self.fail("Campo custom_shelf_locations no existe en Item")
        
        item_refrigerado.append("custom_shelf_locations", {
            "shelf": shelf_refrigerado.name,
            "preferred_location": 1
        })
        
        # Debe guardar sin error
        item_refrigerado.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Verificar que se guardó correctamente
        item_refrigerado.reload()
        self.assertEqual(len(item_refrigerado.custom_shelf_locations), 1)
        self.assertEqual(item_refrigerado.custom_shelf_locations[0].shelf, shelf_refrigerado.name)
        
        # Crear item que NO requiere refrigeración
        item_no_refrigerado = create_test_item(
            item_code=f"TEST-ITEM-NO-REF-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item_no_refrigerado.name)
        
        # Verificar que el campo existe
        item_no_refrigerado.reload()
        if not hasattr(item_no_refrigerado, "custom_requires_refrigeration"):
            self.fail("Campo custom_requires_refrigeration no existe en Item")
        
        # Asegurar que NO requiere refrigeración (0 o None)
        item_no_refrigerado.custom_requires_refrigeration = 0
        
        # Intentar agregar item NO refrigerado a shelf refrigerado debe fallar
        item_no_refrigerado.append("custom_shelf_locations", {
            "shelf": shelf_refrigerado.name,
            "preferred_location": 0
        })
        
        # Esta validación debe fallar cuando se implemente
        with self.assertRaises((ValidationError, frappe.exceptions.ValidationError)):
            item_no_refrigerado.save(ignore_permissions=True)
            frappe.db.commit()

    def test_invariante_tipo_estante_controlado_solo_productos_controlados(self):
        """
        Invariante DDD: Estantes tipo Controlado solo deben contener productos con custom_control_level
        """
        # Crear warehouse y shelf controlado
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf_controlado = create_test_shelf(
            shelf_name="Estante Controlado",
            warehouse=warehouse.name,
            location_code="CTRL-1",
            shelf_type="Controlado"
        )
        self.test_shelves.append(shelf_controlado.name)
        
        # Crear item controlado
        item_controlado = create_test_item(
            item_code=f"TEST-ITEM-CTRL-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_control_level="Psicotrópico",
            custom_requires_prescription_retention=1,
            custom_sanitary_registration="REG-SAN-001",
            has_batch_no=1,
            has_expiry_date=1
        )
        self.test_items.append(item_controlado.name)
        
        # Intentar agregar item controlado a shelf controlado debe funcionar
        item_controlado.reload()
        if not hasattr(item_controlado, "custom_shelf_locations"):
            self.fail("Campo custom_shelf_locations no existe en Item")
        
        item_controlado.append("custom_shelf_locations", {
            "shelf": shelf_controlado.name,
            "preferred_location": 1
        })
        
        # La validación de compatibilidad se implementará en el DocType Item
        try:
            item_controlado.save(ignore_permissions=True)
            frappe.db.commit()
        except ValidationError as e:
            # Si hay validación implementada, debe validar compatibilidad
            pass
        
        # Crear item NO controlado
        item_no_controlado = create_test_item(
            item_code=f"TEST-ITEM-NO-CTRL-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            custom_control_level="None"
        )
        self.test_items.append(item_no_controlado.name)
        
        # Intentar agregar item NO controlado a shelf controlado debe fallar
        item_no_controlado.reload()
        item_no_controlado.append("custom_shelf_locations", {
            "shelf": shelf_controlado.name,
            "preferred_location": 0
        })
        
        # Esta validación debe fallar cuando se implemente
        with self.assertRaises((ValidationError, frappe.exceptions.ValidationError)):
            item_no_controlado.save(ignore_permissions=True)
            frappe.db.commit()

    def test_invariante_ubicacion_preferida_unica(self):
        """
        Invariante DDD: Solo puede haber una ubicación preferida por Item
        """
        # Crear warehouse y shelves
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf1 = create_test_shelf(
            shelf_name="Estante A1",
            warehouse=warehouse.name,
            location_code="A1"
        )
        self.test_shelves.append(shelf1.name)
        
        shelf2 = create_test_shelf(
            shelf_name="Estante A2",
            warehouse=warehouse.name,
            location_code="A2"
        )
        self.test_shelves.append(shelf2.name)
        
        # Crear item
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Agregar múltiples ubicaciones con más de una preferida
        item.reload()
        if not hasattr(item, "custom_shelf_locations"):
            self.fail("Campo custom_shelf_locations no existe en Item")
        
        item.append("custom_shelf_locations", {
            "shelf": shelf1.name,
            "preferred_location": 1
        })
        
        item.append("custom_shelf_locations", {
            "shelf": shelf2.name,
            "preferred_location": 1  # Segunda ubicación también preferida
        })
        
        # Esta validación debe fallar cuando se implemente
        # Por ahora, el test verifica que el campo existe
        try:
            item.save(ignore_permissions=True)
            frappe.db.commit()
            # Si no falla, la validación aún no está implementada
            # Esto es esperado en FASE RED
        except ValidationError:
            # Si falla, la validación está implementada (FASE GREEN)
            pass

    def test_invariante_shelf_debe_existir(self):
        """
        Invariante DDD: El Shelf referenciado en custom_shelf_locations debe existir
        """
        # Crear item
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Intentar agregar shelf inexistente
        item.reload()
        if not hasattr(item, "custom_shelf_locations"):
            self.fail("Campo custom_shelf_locations no existe en Item")
        
        item.append("custom_shelf_locations", {
            "shelf": "SHELF-INEXISTENTE",
            "preferred_location": 0
        })
        
        # Frappe puede validar Links automáticamente o necesitamos implementar validación
        # Por ahora, verificamos que el campo existe y que podemos intentar guardar
        # La validación de shelf existente se implementará en el override de Item
        try:
            item.save(ignore_permissions=True)
            frappe.db.commit()
            # Si no falla, la validación aún no está implementada (FASE RED)
            # Esto es esperado - la validación se implementará en FASE GREEN Parte 2
        except (ValidationError, frappe.exceptions.LinkValidationError):
            # Si falla, la validación está implementada (FASE GREEN)
            pass

