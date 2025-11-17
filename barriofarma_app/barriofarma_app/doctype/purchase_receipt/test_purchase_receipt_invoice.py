# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para conciliación de Purchase Invoice desde Purchase Receipt
BF-007: Solo incluir items con custom_qc_status = "Aceptado"
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
from barriofarma_app.barriofarma_app.overrides.purchase_receipt import make_purchase_invoice


class TestPurchaseReceiptInvoice(unittest.TestCase):
    """Tests unitarios para conciliación Purchase Invoice"""
    
    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_items = []
        self.test_suppliers = []
        self.test_warehouses = []
        self.test_pos = []
        self.test_batches = []
        self.test_prs = []
        self.test_pis = []
    
    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar Purchase Invoices
        for pi_name in self.test_pis:
            try:
                pi = frappe.get_doc("Purchase Invoice", pi_name)
                if pi.docstatus == 1:
                    pi.cancel()
                frappe.delete_doc("Purchase Invoice", pi_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Purchase Receipts
        for pr_name in self.test_prs:
            try:
                pr = frappe.get_doc("Purchase Receipt", pr_name)
                if pr.docstatus == 1:
                    pr.cancel()
                frappe.delete_doc("Purchase Receipt", pr_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Purchase Orders
        for po_name in self.test_pos:
            try:
                po = frappe.get_doc("Purchase Order", po_name)
                if po.docstatus == 1:
                    po.cancel()
                frappe.delete_doc("Purchase Order", po_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Batches
        for batch_name in self.test_batches:
            try:
                frappe.delete_doc("Batch", batch_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Items
        for item_name in self.test_items:
            try:
                frappe.delete_doc("Item", item_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Suppliers
        for supplier_name in self.test_suppliers:
            try:
                frappe.delete_doc("Supplier", supplier_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Warehouses (primero limpiar registros relacionados)
        for warehouse_name in self.test_warehouses:
            try:
                # Limpiar Stock Ledger Entries relacionados
                frappe.db.sql("DELETE FROM `tabStock Ledger Entry` WHERE warehouse = %s", (warehouse_name,))
                # Limpiar Bins relacionados
                frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse = %s", (warehouse_name,))
                # Ahora eliminar el warehouse
                frappe.delete_doc("Warehouse", warehouse_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()
    
    def test_make_purchase_invoice_excluye_rechazados(self):
        """
        Test: Purchase Invoice solo incluye items con custom_qc_status = "Aceptado"
        Items rechazados no deben aparecer en la factura
        """
        # Setup
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
        )
        # Asegurar que has_batch_no se guardó correctamente
        frappe.db.set_value("Item", item.name, "has_batch_no", 1)
        frappe.db.commit()
        item.reload()
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po.name)
        po.submit()
        
        # Crear batches
        batch_a = create_test_batch(item.name, f"BATCH-A-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        batch_b = create_test_batch(item.name, f"BATCH-B-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.extend([batch_a.batch_id, batch_b.batch_id])
        
        # Crear Purchase Receipt con items aceptados y rechazados
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 6,  # Aceptado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_a.batch_id,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 4,  # Rechazado
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
        pr.submit()
        self.test_prs.append(pr.name)
        
        # Crear Purchase Invoice desde Purchase Receipt
        pi = make_purchase_invoice(pr.name)
        pi.insert(ignore_permissions=True)
        self.test_pis.append(pi.name)
        
        # Validar: Solo debe incluir el item aceptado (qty=6)
        self.assertEqual(len(pi.items), 1, "Purchase Invoice debe tener solo 1 item (el aceptado)")
        self.assertEqual(pi.items[0].qty, 6, "Purchase Invoice debe tener cantidad 6 (solo aceptados)")
        self.assertEqual(pi.items[0].item_code, item.name, "Purchase Invoice debe tener el item correcto")
    
    def test_make_purchase_invoice_excluye_cuarentena(self):
        """
        Test: Purchase Invoice excluye items en Cuarentena
        """
        # Setup
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
        )
        # Asegurar que has_batch_no se guardó correctamente
        frappe.db.set_value("Item", item.name, "has_batch_no", 1)
        frappe.db.commit()
        item.reload()
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po.name)
        po.submit()
        
        # Crear batches
        batch_a = create_test_batch(item.name, f"BATCH-A-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        batch_b = create_test_batch(item.name, f"BATCH-B-{frappe.generate_hash(length=6)}", add_months(today(), 10))
        self.test_batches.extend([batch_a.batch_id, batch_b.batch_id])
        
        # Crear Purchase Receipt con items aceptados y en cuarentena
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 7,  # Aceptado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_a.batch_id,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 3,  # Cuarentena
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_b.batch_id,
                    "custom_qc_status": "Cuarentena",
                    "custom_qc_rejection_reason": "Sin evidencia de cadena de frío",
                }
            ]
        })
        pr.insert(ignore_permissions=True)
        pr.submit()
        self.test_prs.append(pr.name)
        
        # Crear Purchase Invoice desde Purchase Receipt
        pi = make_purchase_invoice(pr.name)
        pi.insert(ignore_permissions=True)
        self.test_pis.append(pi.name)
        
        # Validar: Solo debe incluir el item aceptado (qty=7)
        self.assertEqual(len(pi.items), 1, "Purchase Invoice debe tener solo 1 item (el aceptado)")
        self.assertEqual(pi.items[0].qty, 7, "Purchase Invoice debe tener cantidad 7 (solo aceptados)")
        self.assertEqual(pi.items[0].item_code, item.name, "Purchase Invoice debe tener el item correcto")
    
    def test_make_purchase_invoice_solo_aceptados(self):
        """
        Test: Purchase Invoice incluye solo items con custom_qc_status = "Aceptado"
        Si todos los items están aceptados, todos deben aparecer
        """
        # Setup
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
        )
        # Asegurar que has_batch_no se guardó correctamente
        frappe.db.set_value("Item", item.name, "has_batch_no", 1)
        frappe.db.commit()
        item.reload()
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po.name)
        po.submit()
        
        # Crear batches
        batch_a = create_test_batch(item.name, f"BATCH-A-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        batch_b = create_test_batch(item.name, f"BATCH-B-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        self.test_batches.extend([batch_a.batch_id, batch_b.batch_id])
        
        # Crear Purchase Receipt con todos los items aceptados
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 5,  # Aceptado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_a.batch_id,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 5,  # Aceptado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_b.batch_id,
                    "custom_qc_status": "Aceptado",
                }
            ]
        })
        pr.insert(ignore_permissions=True)
        pr.submit()
        self.test_prs.append(pr.name)
        
        # Crear Purchase Invoice desde Purchase Receipt
        pi = make_purchase_invoice(pr.name)
        pi.insert(ignore_permissions=True)
        self.test_pis.append(pi.name)
        
        # Validar: Debe incluir ambos items aceptados
        self.assertEqual(len(pi.items), 2, "Purchase Invoice debe tener 2 items (ambos aceptados)")
        total_qty = sum(item.qty for item in pi.items)
        self.assertEqual(total_qty, 10, "Purchase Invoice debe tener cantidad total 10 (todos aceptados)")

