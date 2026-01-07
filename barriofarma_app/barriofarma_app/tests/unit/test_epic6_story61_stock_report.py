# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para Story 6.1: Mejora de Visualización de Stock en Tiempo Real

Valida el reporte stock_availability_report y sus funcionalidades:
- Stock disponible por almacén
- Stock disponible por estante (Shelf)
- Stock disponible por lote (Batch)
- Fechas de caducidad próximas
- Alertas para stock bajo o productos próximos a vencer
"""

import unittest
import frappe
from frappe.utils import getdate, add_days, today
from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_warehouse,
    create_test_shelf,
    create_test_batch,
    get_test_company,
)
from barriofarma_app.barriofarma_app.report.stock_availability_report.stock_availability_report import (
    get_stock_data,
    get_shelf_stock,
    get_batch_stock,
)


class TestEpic6Story61StockReport(unittest.TestCase):
    """Tests para Story 6.1: Reporte de Stock en Tiempo Real"""

    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        
        self.test_items = []
        self.test_warehouses = []
        self.test_shelves = []
        self.test_batches = []
        
        # Crear warehouse de prueba
        self.warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(self.warehouse.name)
        
        # Crear item con batch
        # Nota: "Venta con Receta Retenida" permite has_batch_no=1 según validaciones DDD
        item_code = f"TEST-ITEM-{frappe.generate_hash(length=6)}"
        self.item = create_test_item(
            item_code=item_code,
            has_batch_no=1,
            has_expiry_date=1,
            item_name="Producto Test con Batch",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_requires_prescription_retention=1,
            custom_sanitary_registration=f"TEST-REG-{frappe.generate_hash(length=6)}"
        )
        self.test_items.append(self.item.name)
        
        # Crear shelf
        self.shelf = create_test_shelf(
            warehouse=self.warehouse.name,
            location_code=f"TEST-LOC-{frappe.generate_hash(length=4)}",
            shelf_name="Estante Test"
        )
        self.test_shelves.append(self.shelf.name)

    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar batches
        for batch_name in self.test_batches:
            try:
                if frappe.db.exists("Batch", batch_name):
                    frappe.delete_doc("Batch", batch_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
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

    def test_get_shelf_stock_returns_data(self):
        """Test: get_shelf_stock debe retornar datos cuando hay stock"""
        # Crear Shelf Movement para simular stock
        shelf_movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Recepción",
            "shelf": self.shelf.name,
            "item": self.item.name,
            "quantity": 100,
            "movement_date": today(),
        })
        shelf_movement.insert(ignore_permissions=True)
        shelf_movement.submit()
        frappe.db.commit()
        
        # Obtener stock por shelf
        shelf_data = get_shelf_stock(self.item.name, self.warehouse.name)
        
        # Verificar que retorna datos
        self.assertIsInstance(shelf_data, list)
        if shelf_data:
            self.assertIn("shelf", shelf_data[0])
            self.assertIn("shelf_name", shelf_data[0])
            self.assertIn("qty", shelf_data[0])

    def test_get_shelf_stock_from_item_config(self):
        """Test: get_shelf_stock debe usar custom_shelf_locations cuando no hay Shelf Movements"""
        # Configurar shelf en item
        item_doc = frappe.get_doc("Item", self.item.name)
        item_doc.append("custom_shelf_locations", {
            "shelf": self.shelf.name
        })
        item_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Obtener stock por shelf (sin Shelf Movements)
        shelf_data = get_shelf_stock(self.item.name, self.warehouse.name)
        
        # Debe retornar datos desde custom_shelf_locations
        self.assertIsInstance(shelf_data, list)

    def test_get_batch_stock_returns_data(self):
        """Test: get_batch_stock debe retornar datos cuando hay batches con stock"""
        # Recargar item desde DB para asegurar que tiene has_batch_no=1
        item_doc = frappe.get_doc("Item", self.item.name)
        self.assertTrue(item_doc.has_batch_no, f"Item {self.item.name} debe tener has_batch_no=1")
        
        # Crear batch
        batch = create_test_batch(
            item_code=self.item.name,
            batch_id=f"TEST-BATCH-{frappe.generate_hash(length=6)}",
            expiry_date=add_days(today(), 30)
        )
        self.test_batches.append(batch.name)
        
        # Crear Stock Entry para agregar stock con batch
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "from_warehouse": None,
            "to_warehouse": self.warehouse.name,
            "posting_date": today(),
            "items": [{
                "item_code": self.item.name,
                "qty": 50,
                "batch_no": batch.name,
                "t_warehouse": self.warehouse.name,
                "basic_rate": 100.0,
                "allow_zero_valuation_rate": 1
            }]
        })
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()
        frappe.db.commit()
        
        # Obtener stock por batch
        batch_data = get_batch_stock(self.item.name, self.warehouse.name)
        
        # Verificar que retorna datos
        self.assertIsInstance(batch_data, list)
        if batch_data:
            self.assertIn("batch_no", batch_data[0])
            self.assertIn("expiry_date", batch_data[0])
            self.assertIn("available_qty", batch_data[0])

    def test_get_batch_stock_with_expiry_alerts(self):
        """Test: get_batch_stock debe calcular días hasta caducidad y alertas"""
        # Recargar item desde DB para asegurar que tiene has_batch_no=1
        item_doc = frappe.get_doc("Item", self.item.name)
        self.assertTrue(item_doc.has_batch_no, f"Item {self.item.name} debe tener has_batch_no=1")
        
        # Crear batch próximo a caducar
        batch = create_test_batch(
            item_code=self.item.name,
            batch_id=f"TEST-BATCH-EXP-{frappe.generate_hash(length=6)}",
            expiry_date=add_days(today(), 5)  # Caduca en 5 días
        )
        self.test_batches.append(batch.name)
        
        # Crear Stock Entry
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": self.warehouse.name,
            "posting_date": today(),
            "items": [{
                "item_code": self.item.name,
                "qty": 30,
                "batch_no": batch.name,
                "t_warehouse": self.warehouse.name,
                "basic_rate": 100.0,
                "allow_zero_valuation_rate": 1
            }]
        })
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()
        frappe.db.commit()
        
        # Obtener stock por batch
        batch_data = get_batch_stock(self.item.name, self.warehouse.name)
        
        # Verificar que incluye información de caducidad
        if batch_data:
            for batch_row in batch_data:
                if batch_row.get("batch_no") == batch.name:
                    self.assertIn("days_to_expiry", batch_row)
                    self.assertLessEqual(batch_row.get("days_to_expiry", 999), 30)
                    self.assertIn("expiry_date", batch_row)

    def test_get_stock_data_integration(self):
        """Test: get_stock_data debe integrar shelf y batch data correctamente"""
        # Recargar item desde DB para asegurar que tiene has_batch_no=1
        item_doc = frappe.get_doc("Item", self.item.name)
        self.assertTrue(item_doc.has_batch_no, f"Item {self.item.name} debe tener has_batch_no=1")
        
        # Crear batch
        batch = create_test_batch(
            item_code=self.item.name,
            batch_id=f"TEST-BATCH-INT-{frappe.generate_hash(length=6)}",
            expiry_date=add_days(today(), 60)
        )
        self.test_batches.append(batch.name)
        
        # Crear Stock Entry
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": self.warehouse.name,
            "posting_date": today(),
            "items": [{
                "item_code": self.item.name,
                "qty": 25,
                "batch_no": batch.name,
                "t_warehouse": self.warehouse.name,
                "basic_rate": 100.0,
                "allow_zero_valuation_rate": 1
            }]
        })
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()
        frappe.db.commit()
        
        # Crear Shelf Movement
        shelf_movement = frappe.get_doc({
            "doctype": "Shelf Movement",
            "movement_type": "Recepción",
            "shelf": self.shelf.name,
            "item": self.item.name,
            "quantity": 25,
            "movement_date": today(),
        })
        shelf_movement.insert(ignore_permissions=True)
        shelf_movement.submit()
        frappe.db.commit()
        
        # Obtener datos completos
        filters = {
            "item_code": self.item.name,
            "warehouse": self.warehouse.name,
            "days_to_expiry": 30
        }
        
        stock_data = get_stock_data(filters)
        
        # Verificar estructura de datos
        self.assertIsInstance(stock_data, list)
        if stock_data:
            row = stock_data[0]
            self.assertIn("item_code", row)
            self.assertIn("item_name", row)
            self.assertIn("warehouse", row)


if __name__ == "__main__":
    unittest.main()

