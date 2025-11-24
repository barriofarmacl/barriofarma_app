# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests E2E para integración Shelf-Stock Entry
Validación de flujo completo de movimiento entre estantes mediante Stock Entry
"""

import unittest
import frappe
from frappe.exceptions import ValidationError
from datetime import datetime

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_warehouse,
    create_test_shelf,
    create_test_item,
    get_test_company,
)


class TestShelfStockEntryE2E(unittest.TestCase):
    """Tests E2E para integración Shelf-Stock Entry"""

    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_shelves = []
        self.test_warehouses = []
        self.test_items = []
        self.test_stock_entries = []
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
        
        # Limpiar stock entries
        for se_name in self.test_stock_entries:
            try:
                if frappe.db.exists("Stock Entry", se_name):
                    frappe.delete_doc("Stock Entry", se_name, force=True, ignore_permissions=True)
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

    def test_e2e_stock_entry_transferencia_entre_estantes(self):
        """
        Test E2E: Crear Stock Entry con transferencia entre estantes
        debe crear automáticamente Shelf Movement
        """
        # Crear warehouse y shelves
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf_origen = create_test_shelf(
            shelf_name="Estante Origen",
            warehouse=warehouse.name,
            location_code="E2E-ORIGEN-1"
        )
        self.test_shelves.append(shelf_origen.name)
        
        shelf_destino = create_test_shelf(
            shelf_name="Estante Destino",
            warehouse=warehouse.name,
            location_code="E2E-DESTINO-1"
        )
        self.test_shelves.append(shelf_destino.name)
        
        # Crear item
        item = create_test_item(
            item_code=f"TEST-ITEM-E2E-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Crear stock inicial en el warehouse mediante Stock Entry de recepción
        stock_entry_recepcion = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": warehouse.name,
            "company": get_test_company(),
            "items": [{
                "item_code": item.name,
                "qty": 20.0,
                "t_warehouse": warehouse.name,
                "allow_zero_valuation_rate": 1,
                "basic_rate": 100.0
            }]
        })
        stock_entry_recepcion.insert(ignore_permissions=True)
        stock_entry_recepcion.submit()
        frappe.db.commit()
        self.test_stock_entries.append(stock_entry_recepcion.name)
        
        # Crear Stock Entry con campos custom_from_shelf y custom_to_shelf
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "from_warehouse": warehouse.name,
            "to_warehouse": warehouse.name,
            "company": get_test_company(),
            "items": [{
                "item_code": item.name,
                "qty": 10.0,
                "s_warehouse": warehouse.name,
                "t_warehouse": warehouse.name,
                "allow_zero_valuation_rate": 1,
                "custom_from_shelf": shelf_origen.name,
                "custom_to_shelf": shelf_destino.name
            }]
        })
        
        # Guardar y enviar Stock Entry
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()
        frappe.db.commit()
        self.test_stock_entries.append(stock_entry.name)
        
        # Verificar que se creó Shelf Movement automáticamente
        movements = frappe.get_all(
            "Shelf Movement",
            filters={
                "reference_doctype": "Stock Entry",
                "reference_name": stock_entry.name
            },
            fields=["name", "movement_type", "shelf", "to_shelf", "item", "quantity"]
        )
        
        self.assertGreater(len(movements), 0, "Debe crearse al menos un Shelf Movement")
        
        # Verificar que el movimiento es de tipo Transferencia
        transfer_movement = [m for m in movements if m.movement_type == "Transferencia"]
        self.assertGreater(len(transfer_movement), 0, "Debe crearse un movimiento tipo Transferencia")
        
        # Verificar shelf origen y destino
        if transfer_movement:
            mov = transfer_movement[0]
            self.assertEqual(mov.shelf, shelf_origen.name, "Shelf origen debe coincidir")
            self.assertEqual(mov.to_shelf, shelf_destino.name, "Shelf destino debe coincidir")
            self.assertEqual(mov.item, item.name, "Item debe coincidir")
            self.assertEqual(mov.quantity, 10.0, "Cantidad debe coincidir")
            self.test_movements.append(mov.name)

    def test_e2e_stock_entry_recepcion_en_estante(self):
        """
        Test E2E: Crear Stock Entry de recepción con estante destino
        debe crear automáticamente Shelf Movement tipo Recepción
        """
        # Crear warehouse y shelf
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante Recepción",
            warehouse=warehouse.name,
            location_code="E2E-RECEP-1"
        )
        self.test_shelves.append(shelf.name)
        
        # Crear item
        item = create_test_item(
            item_code=f"TEST-ITEM-RECEP-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Crear Stock Entry de recepción con custom_to_shelf
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": warehouse.name,
            "company": get_test_company(),
            "items": [{
                "item_code": item.name,
                "qty": 15.0,
                "t_warehouse": warehouse.name,
                "allow_zero_valuation_rate": 1,
                "basic_rate": 100.0,
                "custom_to_shelf": shelf.name
            }]
        })
        
        # Guardar y enviar Stock Entry
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()
        frappe.db.commit()
        self.test_stock_entries.append(stock_entry.name)
        
        # Verificar que se creó Shelf Movement automáticamente
        movements = frappe.get_all(
            "Shelf Movement",
            filters={
                "reference_doctype": "Stock Entry",
                "reference_name": stock_entry.name
            },
            fields=["name", "movement_type", "shelf", "item", "quantity"]
        )
        
        self.assertGreater(len(movements), 0, "Debe crearse al menos un Shelf Movement")
        
        # Verificar que el movimiento es de tipo Recepción
        recep_movement = [m for m in movements if m.movement_type == "Recepción"]
        self.assertGreater(len(recep_movement), 0, "Debe crearse un movimiento tipo Recepción")
        
        # Verificar shelf y cantidad
        if recep_movement:
            mov = recep_movement[0]
            self.assertEqual(mov.shelf, shelf.name, "Shelf debe coincidir")
            self.assertEqual(mov.item, item.name, "Item debe coincidir")
            self.assertEqual(mov.quantity, 15.0, "Cantidad debe coincidir")
            self.test_movements.append(mov.name)

    def test_e2e_stock_entry_validacion_capacidad_estante(self):
        """
        Test E2E: Stock Entry debe validar capacidad del estante antes de transferir
        """
        # Crear warehouse y shelves
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf_origen = create_test_shelf(
            shelf_name="Estante Origen",
            warehouse=warehouse.name,
            location_code="E2E-CAP-ORIGEN"
        )
        self.test_shelves.append(shelf_origen.name)
        
        shelf_destino = create_test_shelf(
            shelf_name="Estante Destino Limitado",
            warehouse=warehouse.name,
            location_code="E2E-CAP-DESTINO",
            capacity_mode="Fija",
            max_capacity=50.0
        )
        self.test_shelves.append(shelf_destino.name)
        
        # Crear item con stock que excede capacidad
        item = create_test_item(
            item_code=f"TEST-ITEM-CAP-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Crear stock en el warehouse
        from erpnext.stock.utils import get_or_make_bin
        bin_name = get_or_make_bin(item.name, warehouse.name)
        bin_doc = frappe.get_doc("Bin", bin_name)
        bin_doc.actual_qty = 60.0  # Excede max_capacity de 50
        bin_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Intentar crear Stock Entry que excede capacidad debe fallar
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "from_warehouse": warehouse.name,
            "to_warehouse": warehouse.name,
            "company": get_test_company(),
            "items": [{
                "item_code": item.name,
                "qty": 60.0,  # Excede capacidad
                "s_warehouse": warehouse.name,
                "t_warehouse": warehouse.name,
                "allow_zero_valuation_rate": 1,
                "custom_from_shelf": shelf_origen.name,
                "custom_to_shelf": shelf_destino.name
            }]
        })
        
        # La validación debe ocurrir en validate(), que se ejecuta al insertar
        with self.assertRaises((ValidationError, frappe.exceptions.ValidationError)):
            stock_entry.insert(ignore_permissions=True)
            frappe.db.commit()

    def test_e2e_stock_entry_validacion_tipo_estante(self):
        """
        Test E2E: Stock Entry debe validar tipo de estante compatible con producto
        """
        # Crear warehouse y shelf refrigerado
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf_refrigerado = create_test_shelf(
            shelf_name="Estante Refrigerado",
            warehouse=warehouse.name,
            location_code="E2E-REF-1",
            shelf_type="Refrigerado"
        )
        self.test_shelves.append(shelf_refrigerado.name)
        
        # Crear item que NO requiere refrigeración
        item = create_test_item(
            item_code=f"TEST-ITEM-NO-REF-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            custom_requires_refrigeration=0
        )
        self.test_items.append(item.name)
        
        # Intentar crear Stock Entry con item no refrigerado en shelf refrigerado debe fallar
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": warehouse.name,
            "company": get_test_company(),
            "items": [{
                "item_code": item.name,
                "qty": 10.0,
                "t_warehouse": warehouse.name,
                "allow_zero_valuation_rate": 1,
                "basic_rate": 100.0,
                "custom_to_shelf": shelf_refrigerado.name
            }]
        })
        
        # La validación ocurre en validate(), que se ejecuta al insertar
        with self.assertRaises((ValidationError, frappe.exceptions.ValidationError)):
            stock_entry.insert(ignore_permissions=True)
            frappe.db.commit()

