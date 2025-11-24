# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests E2E para Purchase Order
Validación del flujo completo de creación y gestión de Purchase Orders
Issue: whiteboard #23 - Fase 2
"""

import unittest
import frappe
from frappe.exceptions import ValidationError

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_warehouse,
    create_test_item,
    create_test_supplier,
    create_test_purchase_order,
    get_test_company,
)


class TestE2EPurchaseOrder(unittest.TestCase):
    """Tests E2E para Purchase Order"""

    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_items = []
        self.test_suppliers = []
        self.test_warehouses = []
        self.test_pos = []
        self.test_prs = []

    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar purchase receipts
        for pr_name in self.test_prs:
            try:
                pr = frappe.get_doc("Purchase Receipt", pr_name)
                if pr.docstatus == 1:
                    pr.cancel()
                frappe.delete_doc("Purchase Receipt", pr_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar purchase orders
        for po_name in self.test_pos:
            try:
                po = frappe.get_doc("Purchase Order", po_name)
                if po.docstatus == 1:
                    po.cancel()
                frappe.delete_doc("Purchase Order", po_name, force=True, ignore_permissions=True)
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
                    # Limpiar Bins relacionados
                    frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse = %s", (warehouse_name,))
                    frappe.delete_doc("Warehouse", warehouse_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar suppliers
        for supplier in self.test_suppliers:
            try:
                if frappe.db.exists("Supplier", supplier.name):
                    frappe.delete_doc("Supplier", supplier.name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()

    def test_e2e_creacion_purchase_order_con_items(self):
        """
        Test E2E: Creación de Purchase Order con items
        1. Crear Purchase Order con múltiples items
        2. Verificar que PO se crea correctamente
        3. Verificar que items están asociados
        4. Verificar que PO puede ser submitted
        """
        # Setup: Crear warehouse
        warehouse = create_test_warehouse(f"TEST-WH-PO-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear items
        item1 = create_test_item(
            item_code=f"TEST-ITEM-PO-1-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item1.name)
        
        item2 = create_test_item(
            item_code=f"TEST-ITEM-PO-2-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item2.name)
        
        # Crear supplier
        supplier = create_test_supplier(f"TEST-SUPPLIER-PO-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        # Crear Purchase Order con múltiples items
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": supplier.name,
            "company": get_test_company(),
            "transaction_date": frappe.utils.today(),
            "schedule_date": frappe.utils.add_days(frappe.utils.today(), 7),
            "items": [
                {
                    "item_code": item1.name,
                    "qty": 100.0,
                    "uom": item1.stock_uom,
                    "rate": 50.0,
                    "schedule_date": frappe.utils.add_days(frappe.utils.today(), 7),
                },
                {
                    "item_code": item2.name,
                    "qty": 50.0,
                    "uom": item2.stock_uom,
                    "rate": 75.0,
                    "schedule_date": frappe.utils.add_days(frappe.utils.today(), 7),
                }
            ]
        })
        
        po.insert(ignore_permissions=True)
        frappe.db.commit()
        self.test_pos.append(po.name)
        
        # Verificar que PO se creó correctamente
        self.assertIsNotNone(po.name, "Purchase Order debe tener nombre")
        self.assertEqual(po.supplier, supplier.name, "Supplier debe coincidir")
        self.assertEqual(len(po.items), 2, "Debe tener 2 items")
        
        # Verificar items asociados
        item_codes = [item.item_code for item in po.items]
        self.assertIn(item1.name, item_codes, "Item 1 debe estar en PO")
        self.assertIn(item2.name, item_codes, "Item 2 debe estar en PO")
        
        # Verificar cantidades
        item1_qty = [item.qty for item in po.items if item.item_code == item1.name][0]
        item2_qty = [item.qty for item in po.items if item.item_code == item2.name][0]
        self.assertEqual(item1_qty, 100.0, "Cantidad item 1 debe ser 100.0")
        self.assertEqual(item2_qty, 50.0, "Cantidad item 2 debe ser 50.0")
        
        # Verificar que PO puede ser submitted
        po.submit()
        frappe.db.commit()
        
        po.reload()
        self.assertEqual(po.docstatus, 1, "Purchase Order debe estar submitted")

    def test_e2e_calculo_stock_necesario_vs_actual(self):
        """
        Test E2E: Cálculo de stock necesario vs stock actual
        1. Crear item con stock actual conocido
        2. Calcular stock necesario (ej: mantener mínimo de 200 unidades)
        3. Crear Purchase Order con cantidad necesaria
        4. Verificar que cantidad en PO refleja la necesidad
        """
        # Setup: Crear warehouse
        warehouse = create_test_warehouse(f"TEST-WH-STOCK-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear item
        item = create_test_item(
            item_code=f"TEST-ITEM-STOCK-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Crear stock inicial en warehouse (50 unidades)
        from erpnext.stock.utils import get_or_make_bin
        bin_name = get_or_make_bin(item.name, warehouse.name)
        bin_doc = frappe.get_doc("Bin", bin_name)
        bin_doc.actual_qty = 50.0
        bin_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Verificar stock actual
        bin_doc.reload()
        stock_actual = bin_doc.actual_qty
        self.assertEqual(stock_actual, 50.0, "Stock actual debe ser 50.0")
        
        # Calcular stock necesario
        # Ejemplo: mantener mínimo de 200 unidades
        stock_minimo_deseado = 200.0
        stock_necesario = stock_minimo_deseado - stock_actual
        
        self.assertEqual(stock_necesario, 150.0, "Stock necesario debe ser 150.0")
        
        # Crear supplier
        supplier = create_test_supplier(f"TEST-SUPPLIER-STOCK-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        # Crear Purchase Order con cantidad necesaria
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": supplier.name,
            "company": get_test_company(),
            "transaction_date": frappe.utils.today(),
            "schedule_date": frappe.utils.add_days(frappe.utils.today(), 7),
            "items": [{
                "item_code": item.name,
                "qty": stock_necesario,  # 150 unidades necesarias
                "uom": item.stock_uom,
                "rate": 100.0,
                "schedule_date": frappe.utils.add_days(frappe.utils.today(), 7),
            }]
        })
        
        po.insert(ignore_permissions=True)
        frappe.db.commit()
        self.test_pos.append(po.name)
        
        # Verificar que cantidad en PO refleja la necesidad
        po_item = po.items[0]
        self.assertEqual(po_item.qty, stock_necesario, "Cantidad en PO debe ser igual al stock necesario")
        self.assertEqual(po_item.qty, 150.0, "Cantidad debe ser 150.0")
        
        # Verificar que después de recibir, el stock alcanzará el mínimo deseado
        # (Esto se verifica en el siguiente test)

    def test_e2e_purchase_receipt_desde_purchase_order(self):
        """
        Test E2E: Purchase Receipt desde Purchase Order
        1. Crear Purchase Order con items
        2. Submit Purchase Order
        3. Crear Purchase Receipt desde PO
        4. Verificar que items se transfieren correctamente
        5. Verificar que stock se actualiza en warehouse
        6. Verificar que PO se marca como recibido parcialmente/completamente
        """
        # Setup: Crear warehouse
        warehouse = create_test_warehouse(f"TEST-WH-PR-PO-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear item
        item = create_test_item(
            item_code=f"TEST-ITEM-PR-PO-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        self.test_items.append(item.name)
        
        # Crear supplier
        supplier = create_test_supplier(f"TEST-SUPPLIER-PR-PO-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        # Paso 1: Crear Purchase Order
        po = frappe.get_doc({
            "doctype": "Purchase Order",
            "supplier": supplier.name,
            "company": get_test_company(),
            "transaction_date": frappe.utils.today(),
            "schedule_date": frappe.utils.add_days(frappe.utils.today(), 7),
            "items": [{
                "item_code": item.name,
                "qty": 100.0,
                "uom": item.stock_uom,
                "rate": 100.0,
                "schedule_date": frappe.utils.add_days(frappe.utils.today(), 7),
            }]
        })
        
        po.insert(ignore_permissions=True)
        po.submit()
        frappe.db.commit()
        self.test_pos.append(po.name)
        
        # Verificar que PO está submitted
        po.reload()
        self.assertEqual(po.docstatus, 1, "Purchase Order debe estar submitted")
        
        # Verificar stock inicial (debe ser 0)
        from erpnext.stock.utils import get_or_make_bin
        bin_name = get_or_make_bin(item.name, warehouse.name)
        bin_doc = frappe.get_doc("Bin", bin_name)
        stock_inicial = bin_doc.actual_qty
        self.assertEqual(stock_inicial, 0.0, "Stock inicial debe ser 0.0")
        
        # Paso 2: Crear Purchase Receipt desde PO
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": get_test_company(),
            "purchase_order": po.name,
            "items": [{
                "item_code": item.name,
                "qty": 100.0,
                "rate": 100.0,
                "warehouse": warehouse.name,
                "purchase_order": po.name,
                "purchase_order_item": po.items[0].name
            }]
        })
        
        pr.insert(ignore_permissions=True)
        pr.submit()
        frappe.db.commit()
        self.test_prs.append(pr.name)
        
        # Verificar que PR está submitted
        pr.reload()
        self.assertEqual(pr.docstatus, 1, "Purchase Receipt debe estar submitted")
        
        # Verificar que PR está vinculado a PO
        self.assertEqual(pr.purchase_order, po.name, "PR debe estar vinculado a PO")
        
        # Paso 3: Verificar que stock se actualiza en warehouse
        bin_doc.reload()
        stock_final = bin_doc.actual_qty
        self.assertEqual(stock_final, 100.0, "Stock final debe ser 100.0")
        
        # Paso 4: Verificar que PO se marca como recibido
        po.reload()
        # Verificar que el item en PO tiene received_qty actualizado
        po_item = po.items[0]
        self.assertEqual(po_item.received_qty, 100.0, "Received qty debe ser 100.0")
        self.assertEqual(po_item.qty, 100.0, "Qty debe ser 100.0")
        
        # Verificar que PO está completamente recibido
        self.assertEqual(po_item.received_qty, po_item.qty, "PO debe estar completamente recibido")

