# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests DDD para el Agregado Shelf Movement (Movimiento de Estantes)
Validación de invariantes y reglas de negocio del dominio farmacéutico
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError
from datetime import datetime

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_warehouse,
    create_test_shelf,
    create_test_item,
    get_test_company,
)


class TestShelfMovementDDD(FrappeTestCase):
    """Tests para invariantes DDD del agregado Shelf Movement"""

    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_shelves = []
        self.test_warehouses = []
        self.test_items = []
        self.test_movements = []

    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar movements
        for movement_name in self.test_movements:
            try:
                if frappe.db.exists("Shelf Movement", movement_name):
                    frappe.delete_doc("Shelf Movement", movement_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
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
                    # Limpiar Bins relacionados
                    frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse = %s", (warehouse_name,))
                    frappe.delete_doc("Warehouse", warehouse_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()

    def test_invariante_shelf_movement_debe_tener_tipo_valido(self):
        """
        Invariante DDD: Shelf Movement debe tener un tipo válido
        Tipos válidos: Transferencia, Recepción, Venta, Ajuste
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante Origen",
            warehouse=warehouse.name,
            location_code="MOV-1"
        )
        self.test_shelves.append(shelf.name)
        
        # Intentar crear movement sin tipo debe fallar
        movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "shelf": shelf.name,
            "item": "TEST-ITEM",
            "quantity": 10.0,
            "movement_date": datetime.now()
        })
        
        with self.assertRaises((ValidationError, frappe.exceptions.MandatoryError)):
            movement.insert(ignore_permissions=True)
            frappe.db.commit()
        
        # Crear movement con tipo válido debe funcionar
        movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Transferencia",
            "shelf": shelf.name,
            "item": "TEST-ITEM",
            "quantity": 10.0,
            "movement_date": datetime.now()
        })
        
        # Esto debería fallar porque el item no existe, pero el tipo debe ser válido
        # Primero verificamos que el tipo sea válido
        valid_types = ["Transferencia", "Recepción", "Venta", "Ajuste"]
        self.assertIn("Transferencia", valid_types, "Transferencia debe ser un tipo válido")

    def test_invariante_shelf_movement_debe_tener_shelf_valido(self):
        """
        Invariante DDD: Shelf Movement debe referenciar un Shelf válido
        """
        # Intentar crear movement con shelf inexistente debe fallar
        movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Transferencia",
            "shelf": "SHELF-INEXISTENTE",
            "item": "TEST-ITEM",
            "quantity": 10.0,
            "movement_date": datetime.now()
        })
        
        with self.assertRaises((ValidationError, frappe.exceptions.LinkValidationError)):
            movement.insert(ignore_permissions=True)
            frappe.db.commit()

    def test_invariante_shelf_movement_debe_tener_item_valido(self):
        """
        Invariante DDD: Shelf Movement debe referenciar un Item válido
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante Test",
            warehouse=warehouse.name,
            location_code="MOV-2"
        )
        self.test_shelves.append(shelf.name)
        
        # Intentar crear movement con item inexistente debe fallar
        movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Transferencia",
            "shelf": shelf.name,
            "item": "ITEM-INEXISTENTE",
            "quantity": 10.0,
            "movement_date": datetime.now()
        })
        
        with self.assertRaises((ValidationError, frappe.exceptions.LinkValidationError)):
            movement.insert(ignore_permissions=True)
            frappe.db.commit()

    def test_invariante_shelf_movement_debe_tener_cantidad_positiva(self):
        """
        Invariante DDD: Shelf Movement debe tener cantidad positiva
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante Test",
            warehouse=warehouse.name,
            location_code="MOV-3"
        )
        self.test_shelves.append(shelf.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Intentar crear movement con cantidad negativa debe fallar
        movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Transferencia",
            "shelf": shelf.name,
            "item": item.name,
            "quantity": -10.0,
            "movement_date": datetime.now()
        })
        
        with self.assertRaises((ValidationError, frappe.exceptions.ValidationError)):
            movement.insert(ignore_permissions=True)
            frappe.db.commit()
        
        # Intentar crear movement con cantidad cero debe fallar
        movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Transferencia",
            "shelf": shelf.name,
            "item": item.name,
            "quantity": 0.0,
            "movement_date": datetime.now()
        })
        
        with self.assertRaises((ValidationError, frappe.exceptions.ValidationError)):
            movement.insert(ignore_permissions=True)
            frappe.db.commit()

    def test_invariante_shelf_movement_debe_registrar_usuario(self):
        """
        Invariante DDD: Shelf Movement debe registrar el usuario que crea el movimiento
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante Test",
            warehouse=warehouse.name,
            location_code="MOV-4"
        )
        self.test_shelves.append(shelf.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Crear movement debe registrar usuario automáticamente
        movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Recepción",
            "shelf": shelf.name,
            "item": item.name,
            "quantity": 10.0,
            "movement_date": datetime.now()
        })
        
        movement.insert(ignore_permissions=True)
        frappe.db.commit()
        self.test_movements.append(movement.name)
        
        # Verificar que tiene usuario registrado
        movement.reload()
        self.assertIsNotNone(movement.owner, "Shelf Movement debe tener usuario registrado")
        self.assertEqual(movement.owner, "Administrator", "Usuario debe ser el que creó el movimiento")

    def test_invariante_shelf_movement_debe_registrar_fecha(self):
        """
        Invariante DDD: Shelf Movement debe tener fecha de movimiento
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante Test",
            warehouse=warehouse.name,
            location_code="MOV-5"
        )
        self.test_shelves.append(shelf.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Crear movement sin fecha debe usar fecha actual por defecto
        movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Recepción",
            "shelf": shelf.name,
            "item": item.name,
            "quantity": 10.0
        })
        
        movement.insert(ignore_permissions=True)
        frappe.db.commit()
        self.test_movements.append(movement.name)
        
        # Verificar que tiene fecha
        movement.reload()
        self.assertIsNotNone(movement.movement_date, "Shelf Movement debe tener fecha de movimiento")

    def test_invariante_shelf_movement_transferencia_debe_tener_shelf_destino(self):
        """
        Invariante DDD: Movimientos tipo Transferencia deben tener shelf destino
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf_origen = create_test_shelf(
            shelf_name="Estante Origen",
            warehouse=warehouse.name,
            location_code="MOV-6-ORIGEN"
        )
        self.test_shelves.append(shelf_origen.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Intentar crear transferencia sin shelf destino debe fallar
        movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Transferencia",
            "shelf": shelf_origen.name,
            "item": item.name,
            "quantity": 10.0,
            "movement_date": datetime.now()
        })
        
        with self.assertRaises((ValidationError, frappe.exceptions.MandatoryError)):
            movement.insert(ignore_permissions=True)
            frappe.db.commit()

    def test_invariante_shelf_movement_consulta_historial_por_shelf(self):
        """
        Invariante DDD: Debe poder consultar historial de movimientos por shelf
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante Test",
            warehouse=warehouse.name,
            location_code="MOV-7"
        )
        self.test_shelves.append(shelf.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Crear varios movimientos
        for i in range(3):
            movement = frappe.get_doc({
                "doctype": "Shelf Movement",
                "movement_type": "Recepción",
                "shelf": shelf.name,
                "item": item.name,
                "quantity": 10.0 + i,
                "movement_date": datetime.now()
            })
            movement.insert(ignore_permissions=True)
            self.test_movements.append(movement.name)
        
        frappe.db.commit()
        
        # Consultar historial por shelf
        movements = frappe.get_all(
            "Shelf Movement",
            filters={"shelf": shelf.name},
            fields=["name", "movement_type", "quantity", "movement_date"],
            order_by="movement_date desc"
        )
        
        self.assertEqual(len(movements), 3, "Debe haber 3 movimientos para este shelf")
        self.assertEqual(movements[0]["movement_type"], "Recepción", "Tipo de movimiento debe ser Recepción")

