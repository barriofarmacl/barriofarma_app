# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para Purchase Receipt con validaciones farmacéuticas
Fase RED del TDD para BF-006
"""

import unittest
import frappe
from frappe.utils import add_months, today

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_supplier,
    create_test_warehouse,
    create_test_purchase_order,
    create_test_batch,
)


class TestPurchaseReceipt(unittest.TestCase):
    """Tests unitarios para Purchase Receipt"""
    
    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_items = []
        self.test_suppliers = []
        self.test_warehouses = []
        self.test_pos = []
        self.test_batches = []
    
    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar Purchase Receipts
        for pr_name in frappe.get_all("Purchase Receipt", filters={"supplier": ("in", [s.name for s in self.test_suppliers])}, pluck="name"):
            try:
                pr = frappe.get_doc("Purchase Receipt", pr_name)
                if pr.docstatus == 1:
                    pr.cancel()
                frappe.delete_doc("Purchase Receipt", pr_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Purchase Orders
        for po_name in [po.name for po in self.test_pos]:
            try:
                po = frappe.get_doc("Purchase Order", po_name)
                if po.docstatus == 1:
                    po.cancel()
                frappe.delete_doc("Purchase Order", po_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Batches
        for batch_id in [b.batch_id for b in self.test_batches]:
            try:
                if frappe.db.exists("Batch", batch_id):
                    frappe.delete_doc("Batch", batch_id, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Items
        for item_name in self.test_items:
            try:
                if frappe.db.exists("Item", item_name):
                    frappe.delete_doc("Item", item_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Suppliers
        for supplier in self.test_suppliers:
            try:
                if frappe.db.exists("Supplier", supplier.name):
                    frappe.delete_doc("Supplier", supplier.name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Warehouses
        for warehouse in self.test_warehouses:
            try:
                if frappe.db.exists("Warehouse", warehouse.name):
                    frappe.delete_doc("Warehouse", warehouse.name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()
    
    def test_purchase_receipt_creacion_basica(self):
        """
        Test: Crear Purchase Receipt básico desde Purchase Order
        """
        # Crear datos de prueba
        item = create_test_item(
            item_code=f"TEST-PR-{frappe.generate_hash(length=6)}",
            item_name="Producto Test PR",
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=0,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po)
        
        # Crear Purchase Receipt
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "uom": item.stock_uom,
                "rate": 100,
                "purchase_order": po.name,
                "purchase_order_item": po.items[0].name,
            }]
        })
        
        pr.insert(ignore_permissions=True)
        
        # Validaciones básicas
        self.assertEqual(pr.items[0].qty, 10)
        self.assertEqual(pr.items[0].item_code, item.name)
        self.assertIsNotNone(pr.name)
        
        # Limpiar
        frappe.delete_doc("Purchase Receipt", pr.name, force=True, ignore_permissions=True)
        frappe.db.commit()
    
    def test_purchase_receipt_con_lote_obligatorio(self):
        """
        Test: Validar que items con has_batch_no=1 requieren lote en Purchase Receipt
        """
        # Crear item que requiere lote
        item = create_test_item(
            item_code=f"TEST-PR-BATCH-{frappe.generate_hash(length=6)}",
            item_name="Producto con Lote",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="F-TEST-001",
            has_batch_no=1,
            has_expiry_date=1,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po)
        
        # Crear batch
        batch = create_test_batch(item.name, f"BATCH-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        self.test_batches.append(batch)
        
        # Crear Purchase Receipt SIN lote (debe fallar)
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "uom": item.stock_uom,
                "rate": 100,
                "purchase_order": po.name,
                "purchase_order_item": po.items[0].name,
                # Sin batch_no - debe fallar porque has_batch_no=1
            }]
        })
        
        # ERPNext valida que items con has_batch_no=1 requieren batch_no
        # Nuestra validación adicional solo aplica para controlados
        with self.assertRaises((frappe.ValidationError, frappe.MandatoryError)):
            pr.insert(ignore_permissions=True)
            pr.save()
        
        frappe.db.rollback()
    
    def test_purchase_receipt_calculo_cantidad_aceptada(self):
        """
        Test: Calcular cantidad aceptada vs rechazada en Purchase Receipt
        Este test fallará inicialmente (RED) hasta implementar la lógica
        """
        # Crear item
        item = create_test_item(
            item_code=f"TEST-PR-QC-{frappe.generate_hash(length=6)}",
            item_name="Producto QC Test",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="F-TEST-002",
            has_batch_no=1,
            has_expiry_date=1,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po)
        
        # Crear batches
        batch_a = create_test_batch(item.name, f"BATCH-A-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        batch_b = create_test_batch(item.name, f"BATCH-B-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.extend([batch_a, batch_b])
        
        # Crear Purchase Receipt con sublotes
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 6,  # Sublote A aceptado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_a.batch_id,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 4,  # Sublote B rechazado (vencimiento corto)
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_b.batch_id,
                    "custom_qc_status": "Rechazado",
                    "custom_qc_rejection_reason": "Vencimiento corto",
                }
            ]
        })
        
        pr.insert(ignore_permissions=True)
        
        # Validar cálculo de cantidad aceptada
        cantidad_aceptada = pr.get_total_accepted_qty()
        cantidad_rechazada = pr.get_total_rejected_qty()
        
        self.assertEqual(cantidad_aceptada, 6)
        self.assertEqual(cantidad_rechazada, 4)
        
        # Limpiar
        frappe.delete_doc("Purchase Receipt", pr.name, force=True, ignore_permissions=True)
        frappe.db.commit()

