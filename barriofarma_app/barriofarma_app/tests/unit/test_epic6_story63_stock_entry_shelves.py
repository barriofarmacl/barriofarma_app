# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para Story 6.3: Optimización de Movimientos de Stock entre Almacenes

Valida las validaciones de Stock Entry con shelves:
- Validación de disponibilidad de stock en estante origen
- Validación de capacidad de estante destino
- Validación de compatibilidad tipo estante-producto
- Validación de que estantes pertenecen a warehouses correctos
- Creación automática de Shelf Movement
"""

import unittest
import frappe
from frappe.exceptions import ValidationError
from frappe.utils import today
from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_warehouse,
    create_test_shelf,
    get_test_company,
)
from barriofarma_app.barriofarma_app.overrides.stock_entry import StockEntry


class TestEpic6Story63StockEntryShelves(unittest.TestCase):
    """Tests para Story 6.3: Validaciones de Stock Entry con Shelves"""

    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        
        self.test_items = []
        self.test_warehouses = []
        self.test_shelves = []
        self.test_stock_entries = []
        
        # Crear warehouses
        self.warehouse_from = create_test_warehouse(f"TEST-WH-FROM-{frappe.generate_hash(length=6)}")
        self.warehouse_to = create_test_warehouse(f"TEST-WH-TO-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(self.warehouse_from.name)
        self.test_warehouses.append(self.warehouse_to.name)
        
        # Crear item
        self.item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            has_batch_no=0,
            item_name="Producto Test",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(self.item.name)
        
        # Crear shelves
        self.shelf_from = create_test_shelf(
            warehouse=self.warehouse_from.name,
            location_code=f"TEST-LOC-FROM-{frappe.generate_hash(length=4)}",
            shelf_name="Estante Origen",
            max_capacity=100
        )
        self.shelf_to = create_test_shelf(
            warehouse=self.warehouse_to.name,
            location_code=f"TEST-LOC-TO-{frappe.generate_hash(length=4)}",
            shelf_name="Estante Destino",
            max_capacity=100
        )
        self.test_shelves.append(self.shelf_from.name)
        self.test_shelves.append(self.shelf_to.name)

    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar Stock Entries
        for se_name in self.test_stock_entries:
            try:
                if frappe.db.exists("Stock Entry", se_name):
                    se = frappe.get_doc("Stock Entry", se_name)
                    if se.docstatus == 1:
                        se.cancel()
                    frappe.delete_doc("Stock Entry", se_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Shelf Movements
        if self.test_stock_entries:
            frappe.db.sql("""
                DELETE FROM `tabShelf Movement`
                WHERE reference_doctype = 'Stock Entry'
                AND reference_name IN %s
            """, (self.test_stock_entries,))
        
        # Limpiar shelves
        for shelf_name in self.test_shelves:
            try:
                if frappe.db.exists("Shelf", shelf_name):
                    frappe.delete_doc("Shelf", shelf_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar items
        for item_name in self.test_items:
            try:
                if frappe.db.exists("Item", item_name):
                    frappe.delete_doc("Item", item_name, force=True, ignore_permissions=True)
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

    def test_validate_shelf_warehouse_match(self):
        """Test: Debe validar que estante pertenece al warehouse correcto"""
        # Crear estante en warehouse diferente
        wrong_warehouse = create_test_warehouse(f"TEST-WH-WRONG-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(wrong_warehouse.name)
        
        wrong_shelf = create_test_shelf(
            warehouse=wrong_warehouse.name,
            location_code=f"TEST-LOC-WRONG-{frappe.generate_hash(length=4)}",
            shelf_name="Estante Incorrecto"
        )
        self.test_shelves.append(wrong_shelf.name)
        
        # Primero agregar stock al warehouse origen para evitar error de valuation
        stock_entry_receipt = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": self.warehouse_from.name,
            "posting_date": today(),
            "items": [{
                "item_code": self.item.name,
                "qty": 50,
                "t_warehouse": self.warehouse_from.name,
                "basic_rate": 100.0,
                "allow_zero_valuation_rate": 1
            }]
        })
        stock_entry_receipt.insert(ignore_permissions=True)
        stock_entry_receipt.submit()
        frappe.db.commit()
        
        # Crear Stock Entry con estante de warehouse incorrecto
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "from_warehouse": self.warehouse_from.name,
            "to_warehouse": self.warehouse_to.name,
            "posting_date": today(),
            "items": [{
                "item_code": self.item.name,
                "qty": 10,
                "s_warehouse": self.warehouse_from.name,
                "t_warehouse": self.warehouse_to.name,
                "custom_from_shelf": wrong_shelf.name,  # Estante de warehouse incorrecto
                "basic_rate": 100.0,
                "allow_zero_valuation_rate": 1
            }]
        })
        
        # Debe lanzar error de validación
        with self.assertRaises(ValidationError) as context:
            stock_entry.insert(ignore_permissions=True)
            stock_entry.validate()
        
        error_msg = str(context.exception)
        # El error debe mencionar que el estante pertenece a otro warehouse
        self.assertTrue(
            "pertenece al almacén" in error_msg or "Incompatibilidad Estante-Almacén" in error_msg,
            f"Error esperado no encontrado. Error real: {error_msg}"
        )

    def test_validate_shelf_capacity(self):
        """Test: Debe validar capacidad de estante destino"""
        # Crear estante con capacidad limitada
        limited_shelf = create_test_shelf(
            warehouse=self.warehouse_to.name,
            location_code=f"TEST-LOC-LIMITED-{frappe.generate_hash(length=4)}",
            shelf_name="Estante Limitado",
            max_capacity=10  # Capacidad muy pequeña
        )
        self.test_shelves.append(limited_shelf.name)
        
        # Crear Stock Entry con cantidad mayor a capacidad
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "from_warehouse": self.warehouse_from.name,
            "to_warehouse": self.warehouse_to.name,
            "posting_date": today(),
            "items": [{
                "item_code": self.item.name,
                "qty": 50,  # Mayor que capacidad (10)
                "s_warehouse": self.warehouse_from.name,
                "t_warehouse": self.warehouse_to.name,
                "custom_to_shelf": limited_shelf.name,
                "basic_rate": 100.0,
                "allow_zero_valuation_rate": 1
            }]
        })
        
        # Debe lanzar error de capacidad
        with self.assertRaises(ValidationError) as context:
            stock_entry.insert(ignore_permissions=True)
            stock_entry.validate()
        
        error_msg = str(context.exception)
        # El mensaje puede variar, verificar que menciona capacidad
        self.assertTrue(
            "Capacidad del Estante Excedida" in error_msg or "excede la capacidad disponible" in error_msg.lower(),
            f"Error esperado no encontrado. Error real: {error_msg}"
        )

    def test_create_shelf_movement_on_submit(self):
        """Test: Debe crear Shelf Movement automáticamente al submit Stock Entry"""
        # Primero agregar stock al warehouse origen
        stock_entry_receipt = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": self.warehouse_from.name,
            "posting_date": today(),
            "items": [{
                "item_code": self.item.name,
                "qty": 50,
                "t_warehouse": self.warehouse_from.name,
                "basic_rate": 100.0,
                "allow_zero_valuation_rate": 1
            }]
        })
        stock_entry_receipt.insert(ignore_permissions=True)
        stock_entry_receipt.submit()
        frappe.db.commit()
        
        # Crear Stock Entry de transferencia con shelves
        # Nota: to_shelf debe pertenecer a to_warehouse, from_shelf a from_warehouse
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "from_warehouse": self.warehouse_from.name,
            "to_warehouse": self.warehouse_to.name,
            "posting_date": today(),
            "items": [{
                "item_code": self.item.name,
                "qty": 20,
                "s_warehouse": self.warehouse_from.name,
                "t_warehouse": self.warehouse_to.name,
                "custom_from_shelf": self.shelf_from.name,  # Pertenece a warehouse_from
                "custom_to_shelf": self.shelf_to.name,  # Pertenece a warehouse_to
                "basic_rate": 100.0,
                "allow_zero_valuation_rate": 1
            }]
        })
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()
        self.test_stock_entries.append(stock_entry.name)
        frappe.db.commit()
        
        # Verificar que se creó Shelf Movement
        shelf_movements = frappe.get_all(
            "Shelf Movement",
            filters={
                "reference_doctype": "Stock Entry",
                "reference_name": stock_entry.name
            }
        )
        
        # Debe haber al menos un Shelf Movement creado
        self.assertGreater(len(shelf_movements), 0)

    def test_validate_shelf_stock_availability(self):
        """Test: Debe validar disponibilidad de stock en estante origen"""
        # Crear Shelf Movement con stock en estante origen
        shelf_movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Recepción",
            "shelf": self.shelf_from.name,
            "item": self.item.name,
            "quantity": 30,  # Stock disponible
            "movement_date": today(),
        })
        shelf_movement.insert(ignore_permissions=True)
        shelf_movement.submit()
        frappe.db.commit()
        
        # Crear Stock Entry intentando transferir más de lo disponible
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "from_warehouse": self.warehouse_from.name,
            "to_warehouse": self.warehouse_to.name,
            "posting_date": today(),
            "items": [{
                "item_code": self.item.name,
                "qty": 50,  # Mayor que stock disponible (30)
                "s_warehouse": self.warehouse_from.name,
                "t_warehouse": self.warehouse_to.name,
                "custom_from_shelf": self.shelf_from.name,
                "basic_rate": 100.0,
                "allow_zero_valuation_rate": 1
            }]
        })
        
        # Debe lanzar error de stock insuficiente
        with self.assertRaises(ValidationError) as context:
            stock_entry.insert(ignore_permissions=True)
            stock_entry.validate()
        
        error_msg = str(context.exception)
        # El mensaje puede variar, verificar que menciona stock insuficiente
        self.assertTrue(
            "Stock Insuficiente" in error_msg or "stock suficiente" in error_msg.lower(),
            f"Error esperado no encontrado. Error real: {error_msg}"
        )


if __name__ == "__main__":
    unittest.main()

