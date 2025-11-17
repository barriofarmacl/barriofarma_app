# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests DDD para invariantes de conciliación de Purchase Invoice
BF-007: Invariante "No pagar rechazados/cuarentena"
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


class TestPurchaseReceiptInvoiceDDD(unittest.TestCase):
    """Tests DDD para invariantes de conciliación"""
    
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
    
    def test_invariante_no_pagar_rechazados(self):
        """
        Invariante DDD: No pagar rechazados
        Purchase Invoice NO debe incluir items con custom_qc_status = "Rechazado"
        """
        # Setup
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
        )
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
        
        batch_rechazado = create_test_batch(item.name, f"BATCH-REJECT-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch_rechazado.batch_id)
        
        # Crear Purchase Receipt con item rechazado
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
                "batch_no": batch_rechazado.batch_id,
                "custom_qc_status": "Rechazado",
                "custom_qc_rejection_reason": "Vencimiento corto",
            }]
        })
        pr.insert(ignore_permissions=True)
        pr.submit()
        self.test_prs.append(pr.name)
        
        # Crear Purchase Invoice desde Purchase Receipt
        # Debe lanzar error porque todos los items están rechazados
        with self.assertRaises(frappe.ValidationError) as context:
            pi = make_purchase_invoice(pr.name)
            pi.insert(ignore_permissions=True)
        
        # Validar que el error es el esperado
        error_msg = str(context.exception)
        self.assertIn("Rechazados o en Cuarentena", error_msg, "Debe lanzar error cuando todos los items están rechazados")
    
    def test_invariante_no_pagar_cuarentena(self):
        """
        Invariante DDD: No pagar cuarentena
        Purchase Invoice NO debe incluir items con custom_qc_status = "Cuarentena"
        """
        # Setup
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
        )
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
        
        batch_cuarentena = create_test_batch(item.name, f"BATCH-QUAR-{frappe.generate_hash(length=6)}", add_months(today(), 10))
        self.test_batches.append(batch_cuarentena.batch_id)
        
        # Crear Purchase Receipt con item en cuarentena
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
                "batch_no": batch_cuarentena.batch_id,
                "custom_qc_status": "Cuarentena",
                "custom_qc_rejection_reason": "Sin evidencia de cadena de frío",
            }]
        })
        pr.insert(ignore_permissions=True)
        pr.submit()
        self.test_prs.append(pr.name)
        
        # Crear Purchase Invoice desde Purchase Receipt
        # Debe lanzar error porque todos los items están en cuarentena
        with self.assertRaises(frappe.ValidationError) as context:
            pi = make_purchase_invoice(pr.name)
            pi.insert(ignore_permissions=True)
        
        # Validar que el error es el esperado
        error_msg = str(context.exception)
        self.assertIn("Rechazados o en Cuarentena", error_msg, "Debe lanzar error cuando todos los items están en cuarentena")
    
    def test_invariante_solo_pagar_aceptados(self):
        """
        Invariante DDD: Solo pagar aceptados
        Purchase Invoice SOLO debe incluir items con custom_qc_status = "Aceptado"
        """
        # Setup
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
        )
        frappe.db.set_value("Item", item.name, "has_batch_no", 1)
        frappe.db.commit()
        item.reload()
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        po = create_test_purchase_order(item.name, qty=20, supplier_name=supplier.name)
        self.test_pos.append(po.name)
        po.submit()
        
        batch_aceptado = create_test_batch(item.name, f"BATCH-ACCEPT-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        batch_rechazado = create_test_batch(item.name, f"BATCH-REJECT-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.extend([batch_aceptado.batch_id, batch_rechazado.batch_id])
        
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
                    "qty": 12,  # Aceptado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_aceptado.batch_id,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 8,  # Rechazado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_rechazado.batch_id,
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
        
        # Validar invariante: SOLO debe incluir items aceptados
        self.assertEqual(len(pi.items), 1, "Purchase Invoice debe tener solo 1 item (el aceptado)")
        self.assertEqual(pi.items[0].qty, 12, "Purchase Invoice debe tener cantidad 12 (solo aceptados)")
        self.assertEqual(pi.items[0].item_code, item.name, "Purchase Invoice debe tener el item correcto")
        
        # Validar que el total de la factura corresponde solo a los aceptados
        total_esperado = 12 * 100  # Solo los 12 aceptados
        self.assertEqual(pi.total, total_esperado, f"Purchase Invoice total debe ser {total_esperado} (solo aceptados)")
    
    def test_invariante_conciliacion_excluye_rechazados_cuarentena(self):
        """
        Invariante DDD: Conciliación excluye rechazados y cuarentena
        Purchase Invoice debe excluir TODOS los items no aceptados, independientemente de la razón
        """
        # Setup
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
        )
        frappe.db.set_value("Item", item.name, "has_batch_no", 1)
        frappe.db.commit()
        item.reload()
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        po = create_test_purchase_order(item.name, qty=30, supplier_name=supplier.name)
        self.test_pos.append(po.name)
        po.submit()
        
        batch_aceptado = create_test_batch(item.name, f"BATCH-ACCEPT-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        batch_rechazado = create_test_batch(item.name, f"BATCH-REJECT-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        batch_cuarentena = create_test_batch(item.name, f"BATCH-QUAR-{frappe.generate_hash(length=6)}", add_months(today(), 10))
        self.test_batches.extend([batch_aceptado.batch_id, batch_rechazado.batch_id, batch_cuarentena.batch_id])
        
        # Crear Purchase Receipt con items aceptados, rechazados y en cuarentena
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 10,  # Aceptado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_aceptado.batch_id,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 8,  # Rechazado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_rechazado.batch_id,
                    "custom_qc_status": "Rechazado",
                    "custom_qc_rejection_reason": "Vencimiento corto",
                },
                {
                    "item_code": item.name,
                    "qty": 12,  # Cuarentena
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_cuarentena.batch_id,
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
        
        # Validar invariante: SOLO debe incluir items aceptados
        self.assertEqual(len(pi.items), 1, "Purchase Invoice debe tener solo 1 item (el aceptado)")
        self.assertEqual(pi.items[0].qty, 10, "Purchase Invoice debe tener cantidad 10 (solo aceptados)")
        
        # Validar que rechazados y cuarentena NO están en la factura
        item_codes_en_factura = [item.item_code for item in pi.items]
        # Todos los items son del mismo producto, pero solo debe haber 1 línea con qty=10
        total_qty_facturada = sum(item.qty for item in pi.items)
        self.assertEqual(total_qty_facturada, 10, "Total facturado debe ser 10 (solo aceptados, excluyendo rechazados y cuarentena)")
        
        # Validar total de la factura
        total_esperado = 10 * 100  # Solo los 10 aceptados
        self.assertEqual(pi.total, total_esperado, f"Purchase Invoice total debe ser {total_esperado} (solo aceptados, excluyendo rechazados y cuarentena)")

