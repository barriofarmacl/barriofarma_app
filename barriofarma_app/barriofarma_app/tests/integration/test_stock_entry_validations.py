# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests Unitarios para Validaciones DDD de Stock Entry
Story 9.1: Tests Unitarios para Validaciones DDD

Cubre las validaciones en barriofarma_app/overrides/stock_entry.py:
- validate_shelf_capacity_and_type
  - _validate_shelf_capacity
  - _validate_shelf_item_compatibility
  - _validate_shelf_warehouse_match
  - _validate_shelf_stock_availability
- create_shelf_movements (on_submit)
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_warehouse,
    create_test_shelf,
    get_test_company,
)


class TestStockEntryValidations(FrappeTestCase):
    """Tests unitarios para validaciones DDD de Stock Entry"""
    
    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_items = []
        self.test_warehouses = []
        self.test_shelves = []
        self.test_stock_entries = []
    
    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar Stock Entries
        for se_name in self.test_stock_entries:
            try:
                se = frappe.get_doc("Stock Entry", se_name)
                if se.docstatus == 1:
                    se.cancel()
                frappe.delete_doc("Stock Entry", se_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Shelves
        for shelf_name in self.test_shelves:
            try:
                frappe.delete_doc("Shelf", shelf_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Items
        for item_name in self.test_items:
            try:
                frappe.delete_doc("Item", item_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Warehouses
        for warehouse_name in self.test_warehouses:
            try:
                frappe.db.sql("DELETE FROM `tabStock Ledger Entry` WHERE warehouse = %s", (warehouse_name,))
                frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse = %s", (warehouse_name,))
                frappe.delete_doc("Warehouse", warehouse_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()
    
    # ========================================
    # TESTS: _validate_shelf_capacity
    # ========================================
    
    def test_shelf_capacity_exceeded_should_fail(self):
        """
        Validación: Stock Entry debe fallar si la cantidad excede la capacidad del estante
        """
        company = get_test_company()
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.append(warehouse.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
        )
        self.test_items.append(item.name)
        
        # Crear estante con capacidad limitada
        shelf = create_test_shelf(
            shelf_name=f"TEST-SHELF-{frappe.generate_hash(length=6)}",
            warehouse=warehouse.name,
            location_code=f"LOC-{frappe.generate_hash(length=6)}",
            capacity_mode="Fija",
            max_capacity=100.0,
        )
        self.test_shelves.append(shelf.name)
        
        # Crear Stock Entry con cantidad que excede capacidad
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": today(),
            "to_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 150,  # Excede capacidad de 100
                "t_warehouse": warehouse.name,
                "custom_to_shelf": shelf.name,
                "allow_zero_valuation_rate": 1,  # Evitar error de valuation rate
            }]
        })
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError) as context:
            se.insert(ignore_permissions=True)
            se.validate()
        
        error_msg = str(context.exception)
        self.assertIn("capacidad", error_msg.lower(), "Debe indicar que se excedió la capacidad")
    
    def test_shelf_capacity_within_limit_should_pass(self):
        """
        Validación: Stock Entry debe pasar si la cantidad está dentro de la capacidad del estante
        """
        company = get_test_company()
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.append(warehouse.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
        )
        self.test_items.append(item.name)
        
        # Crear estante con capacidad suficiente
        shelf = create_test_shelf(
            shelf_name=f"TEST-SHELF-{frappe.generate_hash(length=6)}",
            warehouse=warehouse.name,
            location_code=f"LOC-{frappe.generate_hash(length=6)}",
            capacity_mode="Fija",
            max_capacity=100.0,
        )
        self.test_shelves.append(shelf.name)
        
        # Crear Stock Entry con cantidad dentro de capacidad
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": today(),
            "to_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 50,  # Dentro de capacidad de 100
                "t_warehouse": warehouse.name,
                "custom_to_shelf": shelf.name,
                "allow_zero_valuation_rate": 1,  # Evitar error de valuation rate
            }]
        })
        
        # No debe lanzar error
        se.insert(ignore_permissions=True)
        self.test_stock_entries.append(se.name)
        self.assertIsNotNone(se.name, "Stock Entry debe crearse si la capacidad es suficiente")
    
    # ========================================
    # TESTS: _validate_shelf_item_compatibility
    # ========================================
    
    def test_refrigerated_shelf_requires_refrigeration(self):
        """
        Validación: Estante Refrigerado solo puede contener productos que requieren refrigeración
        """
        company = get_test_company()
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.append(warehouse.name)
        
        # Item sin refrigeración
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            custom_requires_refrigeration=0,
        )
        self.test_items.append(item.name)
        
        # Crear estante Refrigerado
        shelf = create_test_shelf(
            shelf_name=f"TEST-SHELF-{frappe.generate_hash(length=6)}",
            warehouse=warehouse.name,
            location_code=f"LOC-{frappe.generate_hash(length=6)}",
            shelf_type="Refrigerado",
        )
        self.test_shelves.append(shelf.name)
        
        # Crear Stock Entry con item sin refrigeración en estante refrigerado
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": today(),
            "to_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "t_warehouse": warehouse.name,
                "custom_to_shelf": shelf.name,
                "allow_zero_valuation_rate": 1,  # Evitar error de valuation rate
            }]
        })
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError) as context:
            se.insert(ignore_permissions=True)
            se.validate()
        
        error_msg = str(context.exception)
        self.assertIn("refrigerado", error_msg.lower(), "Debe indicar incompatibilidad con estante refrigerado")
    
    def test_refrigerated_shelf_with_refrigerated_item_should_pass(self):
        """
        Validación: Estante Refrigerado puede contener productos que requieren refrigeración
        """
        company = get_test_company()
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.append(warehouse.name)
        
        # Item con refrigeración
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            custom_requires_refrigeration=1,
        )
        self.test_items.append(item.name)
        
        # Crear estante Refrigerado
        shelf = create_test_shelf(
            shelf_name=f"TEST-SHELF-{frappe.generate_hash(length=6)}",
            warehouse=warehouse.name,
            location_code=f"LOC-{frappe.generate_hash(length=6)}",
            shelf_type="Refrigerado",
        )
        self.test_shelves.append(shelf.name)
        
        # Crear Stock Entry con item refrigerado en estante refrigerado
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": today(),
            "to_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "t_warehouse": warehouse.name,
                "custom_to_shelf": shelf.name,
            }]
        })
        
        # No debe lanzar error
        se.insert(ignore_permissions=True)
        self.test_stock_entries.append(se.name)
        self.assertIsNotNone(se.name, "Item refrigerado debe poder ir en estante refrigerado")
    
    def test_controlled_shelf_requires_control_level(self):
        """
        Validación: Estante Controlado solo puede contener productos con nivel de control
        """
        company = get_test_company()
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.append(warehouse.name)
        
        # Item sin nivel de control
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            custom_control_level="None",
        )
        self.test_items.append(item.name)
        
        # Crear estante Controlado
        shelf = create_test_shelf(
            shelf_name=f"TEST-SHELF-{frappe.generate_hash(length=6)}",
            warehouse=warehouse.name,
            location_code=f"LOC-{frappe.generate_hash(length=6)}",
            shelf_type="Controlado",
        )
        self.test_shelves.append(shelf.name)
        
        # Crear Stock Entry con item sin control en estante controlado
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": today(),
            "to_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "t_warehouse": warehouse.name,
                "custom_to_shelf": shelf.name,
                "allow_zero_valuation_rate": 1,  # Evitar error de valuation rate
            }]
        })
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError) as context:
            se.insert(ignore_permissions=True)
            se.validate()
        
        error_msg = str(context.exception)
        self.assertIn("control", error_msg.lower(), "Debe indicar incompatibilidad con estante controlado")
    
    def test_controlled_shelf_with_controlled_item_should_pass(self):
        """
        Validación: Estante Controlado puede contener productos con nivel de control
        """
        company = get_test_company()
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.append(warehouse.name)
        
        # Item con nivel de control
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_control_level="Psicotrópico",
            custom_sanitary_registration="F-CTRL-001",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1,
        )
        self.test_items.append(item.name)
        
        # Crear estante Controlado
        shelf = create_test_shelf(
            shelf_name=f"TEST-SHELF-{frappe.generate_hash(length=6)}",
            warehouse=warehouse.name,
            location_code=f"LOC-{frappe.generate_hash(length=6)}",
            shelf_type="Controlado",
        )
        self.test_shelves.append(shelf.name)
        
        # Crear Stock Entry con item controlado en estante controlado
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": today(),
            "to_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "t_warehouse": warehouse.name,
                "custom_to_shelf": shelf.name,
            }]
        })
        
        # No debe lanzar error
        se.insert(ignore_permissions=True)
        self.test_stock_entries.append(se.name)
        self.assertIsNotNone(se.name, "Item controlado debe poder ir en estante controlado")
    
    # ========================================
    # TESTS: _validate_shelf_warehouse_match
    # ========================================
    
    def test_shelf_warehouse_mismatch_should_fail(self):
        """
        Validación: Estante debe pertenecer al warehouse del Stock Entry
        """
        company = get_test_company()
        warehouse1 = create_test_warehouse(f"TEST-WH-1-{frappe.generate_hash(length=6)}", company=company)
        warehouse2 = create_test_warehouse(f"TEST-WH-2-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.extend([warehouse1.name, warehouse2.name])
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
        )
        self.test_items.append(item.name)
        
        # Crear estante en warehouse1
        shelf = create_test_shelf(
            shelf_name=f"TEST-SHELF-{frappe.generate_hash(length=6)}",
            warehouse=warehouse1.name,
            location_code=f"LOC-{frappe.generate_hash(length=6)}",
        )
        self.test_shelves.append(shelf.name)
        
        # Crear Stock Entry con warehouse2 pero estante de warehouse1
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": today(),
            "to_warehouse": warehouse2.name,  # Warehouse diferente
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "t_warehouse": warehouse2.name,
                "custom_to_shelf": shelf.name,  # Estante de warehouse1
            }]
        })
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError) as context:
            se.insert(ignore_permissions=True)
            se.validate()
        
        error_msg = str(context.exception)
        self.assertIn("almacén", error_msg.lower(), "Debe indicar incompatibilidad de warehouse")
    
    def test_shelf_warehouse_match_should_pass(self):
        """
        Validación: Estante que pertenece al warehouse del Stock Entry debe pasar
        """
        company = get_test_company()
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.append(warehouse.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
        )
        self.test_items.append(item.name)
        
        # Crear estante en el mismo warehouse
        shelf = create_test_shelf(
            shelf_name=f"TEST-SHELF-{frappe.generate_hash(length=6)}",
            warehouse=warehouse.name,
            location_code=f"LOC-{frappe.generate_hash(length=6)}",
        )
        self.test_shelves.append(shelf.name)
        
        # Crear Stock Entry con warehouse y estante coincidentes
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": today(),
            "to_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "t_warehouse": warehouse.name,
                "custom_to_shelf": shelf.name,
            }]
        })
        
        # No debe lanzar error
        se.insert(ignore_permissions=True)
        self.test_stock_entries.append(se.name)
        self.assertIsNotNone(se.name, "Estante y warehouse coincidentes deben pasar")
    
    # ========================================
    # TESTS: _validate_shelf_stock_availability
    # ========================================
    
    def test_stock_entry_without_shelf_should_fail(self):
        """
        Regla #58: Stock Entry con movimiento de stock exige estante origen y destino.
        """
        company = get_test_company()
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.append(warehouse.name)

        shelf = create_test_shelf(
            shelf_name=f"TEST-SHELF-{frappe.generate_hash(length=6)}",
            warehouse=warehouse.name,
            location_code=f"LOC-{frappe.generate_hash(length=6)}",
        )
        self.test_shelves.append(shelf.name)

        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
        )
        self.test_items.append(item.name)

        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "company": company,
            "posting_date": today(),
            "from_warehouse": warehouse.name,
            "to_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "s_warehouse": warehouse.name,
                "t_warehouse": warehouse.name,
                "allow_zero_valuation_rate": 1,
            }]
        })

        with self.assertRaises(frappe.ValidationError):
            se.insert(ignore_permissions=True)

    def test_stock_entry_warehouse_without_shelves_should_fail(self):
        """Almacén sin estantes activos no puede recibir movimientos de stock."""
        company = get_test_company()
        warehouse = create_test_warehouse(f"TEST-WH-NOSHELF-{frappe.generate_hash(length=6)}", company=company)
        self.test_warehouses.append(warehouse.name)

        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
        )
        self.test_items.append(item.name)

        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": today(),
            "to_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 5,
                "t_warehouse": warehouse.name,
            }]
        })

        with self.assertRaises(frappe.ValidationError):
            se.insert(ignore_permissions=True)

