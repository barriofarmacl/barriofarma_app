# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests E2E para BF-008: Política de umbral de vencimiento configurable
Flujo completo: recepción con sublote bajo umbral → cuarentena automática
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
    get_test_company,
)


class TestBF008UmbralVencimiento(unittest.TestCase):
    """Tests E2E para umbral de vencimiento configurable"""
    
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
        self.test_item_groups = []
    
    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
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
        
        # Limpiar Warehouses
        for warehouse_name in self.test_warehouses:
            try:
                frappe.db.sql("DELETE FROM `tabStock Ledger Entry` WHERE warehouse = %s", (warehouse_name,))
                frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse = %s", (warehouse_name,))
                frappe.delete_doc("Warehouse", warehouse_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar Item Groups
        for item_group_name in self.test_item_groups:
            try:
                frappe.delete_doc("Item Group", item_group_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()
    
    def test_e2e_recepcion_sublote_bajo_umbral_cuarentena(self):
        """
        Scenario E2E: Recepción con sublote bajo umbral → Cuarentena automática
        Gherkin:
          Given un Item Group con umbral de 6 meses
          And una Purchase Order de 10 unidades
          When se recibe con sublote de 2 meses de vencimiento
          Then el sublote queda automáticamente en Cuarentena
        """
        # Setup
        company_name = get_test_company()
        
        # Given: Item Group con umbral de 6 meses
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": f"TEST-IG-{frappe.generate_hash(length=6)}",
            "is_group": 0,
        })
        item_group.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.db.set_value("Item Group", item_group.name, "custom_minimum_expiry_months", 6)
        frappe.db.commit()
        item_group.reload()
        self.test_item_groups.append(item_group.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
            item_group=item_group.name,
        )
        frappe.db.set_value("Item", item.name, "has_batch_no", 1)
        frappe.db.commit()
        item.reload()
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company_name)
        self.test_warehouses.append(warehouse.name)
        
        # Given: Purchase Order de 10 unidades
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name, rate=100)
        self.test_pos.append(po.name)
        po.submit()
        
        # When: Se recibe con sublote de 2 meses de vencimiento (bajo umbral de 6)
        batch_corto = create_test_batch(item.name, f"BATCH-CORTO-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch_corto.batch_id)
        
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": company_name,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 10,
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_corto.batch_id,
                    "custom_qc_status": "Aceptado",  # Inicialmente aceptado
                }
            ]
        })
        pr.insert(ignore_permissions=True)
        pr.validate()  # Esto ejecuta validate_umbral_vencimiento
        pr.save()
        self.test_prs.append(pr.name)
        
        # Then: El sublote queda automáticamente en Cuarentena
        pr.reload()
        self.assertEqual(pr.items[0].custom_qc_status, "Cuarentena", "Sublote con vencimiento corto debe quedar en Cuarentena automáticamente")
        self.assertEqual(pr.items[0].custom_qc_rejection_reason, "Vencimiento corto", "Debe tener causa de cuarentena")
    
    def test_e2e_recepcion_sublote_sobre_umbral_aceptado(self):
        """
        Scenario E2E: Recepción con sublote sobre umbral → Aceptado
        Gherkin:
          Given un Item Group con umbral de 6 meses
          And una Purchase Order de 10 unidades
          When se recibe con sublote de 12 meses de vencimiento
          Then el sublote queda Aceptado
        """
        # Setup
        company_name = get_test_company()
        
        # Given: Item Group con umbral de 6 meses
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": f"TEST-IG-{frappe.generate_hash(length=6)}",
            "is_group": 0,
        })
        item_group.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.db.set_value("Item Group", item_group.name, "custom_minimum_expiry_months", 6)
        frappe.db.commit()
        item_group.reload()
        self.test_item_groups.append(item_group.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
            item_group=item_group.name,
        )
        frappe.db.set_value("Item", item.name, "has_batch_no", 1)
        frappe.db.commit()
        item.reload()
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company_name)
        self.test_warehouses.append(warehouse.name)
        
        # Given: Purchase Order de 10 unidades
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name, rate=100)
        self.test_pos.append(po.name)
        po.submit()
        
        # When: Se recibe con sublote de 12 meses de vencimiento (sobre umbral de 6)
        batch_largo = create_test_batch(item.name, f"BATCH-LARGO-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        self.test_batches.append(batch_largo.batch_id)
        
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": company_name,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 10,
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_largo.batch_id,
                    "custom_qc_status": "Aceptado",
                }
            ]
        })
        pr.insert(ignore_permissions=True)
        pr.validate()  # Esto ejecuta validate_umbral_vencimiento
        pr.save()
        self.test_prs.append(pr.name)
        
        # Then: El sublote queda Aceptado
        pr.reload()
        # Verificar que el umbral es 6 meses y el vencimiento es 12 meses
        threshold = pr.get_minimum_expiry_months(item.name)
        self.assertGreaterEqual(threshold, 6, f"Umbral debe ser al menos 6 meses, pero es {threshold}")
        self.assertEqual(pr.items[0].custom_qc_status, "Aceptado", f"Sublote con vencimiento largo (12 meses) debe quedar Aceptado si umbral es {threshold}. Estado actual: {pr.items[0].custom_qc_status}")
        # El campo puede tener valor previo, así que solo verificamos que no sea "Vencimiento corto"
        if pr.items[0].custom_qc_rejection_reason:
            self.assertNotEqual(pr.items[0].custom_qc_rejection_reason, "Vencimiento corto", "No debe tener causa 'Vencimiento corto' si el vencimiento es largo")
    
    def test_e2e_recepcion_multiple_sublotes_umbral_diferente(self):
        """
        Scenario E2E: Recepción con múltiples sublotes, algunos bajo umbral
        Gherkin:
          Given un Item Group con umbral de 6 meses
          And una Purchase Order de 20 unidades
          When se recibe con 2 sublotes: uno de 2 meses y otro de 12 meses
          Then el sublote corto queda en Cuarentena y el largo queda Aceptado
        """
        # Setup
        company_name = get_test_company()
        
        # Given: Item Group con umbral de 6 meses
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": f"TEST-IG-{frappe.generate_hash(length=6)}",
            "is_group": 0,
        })
        item_group.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.db.set_value("Item Group", item_group.name, "custom_minimum_expiry_months", 6)
        frappe.db.commit()
        item_group.reload()
        self.test_item_groups.append(item_group.name)
        
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=1,
            item_group=item_group.name,
        )
        frappe.db.set_value("Item", item.name, "has_batch_no", 1)
        frappe.db.commit()
        item.reload()
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company_name)
        self.test_warehouses.append(warehouse.name)
        
        # Given: Purchase Order de 20 unidades
        po = create_test_purchase_order(item.name, qty=20, supplier_name=supplier.name, rate=100)
        self.test_pos.append(po.name)
        po.submit()
        
        # When: Se recibe con 2 sublotes
        batch_corto = create_test_batch(item.name, f"BATCH-CORTO-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        batch_largo = create_test_batch(item.name, f"BATCH-LARGO-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        self.test_batches.extend([batch_corto.batch_id, batch_largo.batch_id])
        
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": company_name,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 10,
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_corto.batch_id,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 10,
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_largo.batch_id,
                    "custom_qc_status": "Aceptado",
                }
            ]
        })
        pr.insert(ignore_permissions=True)
        pr.validate()  # Esto ejecuta validate_umbral_vencimiento
        pr.save()
        self.test_prs.append(pr.name)
        
        # Then: El sublote corto queda en Cuarentena y el largo queda Aceptado
        pr.reload()
        item_corto = [item for item in pr.items if item.batch_no == batch_corto.batch_id][0]
        item_largo = [item for item in pr.items if item.batch_no == batch_largo.batch_id][0]
        
        self.assertEqual(item_corto.custom_qc_status, "Cuarentena", "Sublote corto debe quedar en Cuarentena")
        self.assertEqual(item_corto.custom_qc_rejection_reason, "Vencimiento corto", "Debe tener causa de cuarentena")
        
        self.assertEqual(item_largo.custom_qc_status, "Aceptado", "Sublote largo debe quedar Aceptado")
        # El campo puede tener valor previo, así que solo verificamos que no sea "Vencimiento corto"
        if item_largo.custom_qc_rejection_reason:
            self.assertNotEqual(item_largo.custom_qc_rejection_reason, "Vencimiento corto", "No debe tener causa 'Vencimiento corto' si el vencimiento es largo")

