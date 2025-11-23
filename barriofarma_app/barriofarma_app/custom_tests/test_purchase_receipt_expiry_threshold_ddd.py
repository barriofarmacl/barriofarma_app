# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests DDD para BF-008: Política de umbral de vencimiento configurable
Validar invariantes del dominio: cuarentena/rechazo por vencimiento corto
"""

import unittest
import frappe
from frappe.utils import add_months, today, getdate

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_supplier,
    create_test_warehouse,
    create_test_purchase_order,
    create_test_batch,
    get_test_company,
)


class TestPurchaseReceiptExpiryThresholdDDD(unittest.TestCase):
    """Tests DDD para política de umbral de vencimiento"""
    
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
    
    def test_invariante_umbral_vencimiento_cuarentena(self):
        """
        Invariante DDD: Items con vencimiento bajo umbral quedan automáticamente en Cuarentena
        """
        # Setup
        company_name = get_test_company()
        
        # Crear Item Group con umbral de 6 meses
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": f"TEST-IG-{frappe.generate_hash(length=6)}",
            "is_group": 0,
        })
        item_group.insert(ignore_permissions=True)
        frappe.db.commit()
        # Configurar umbral después de insertar
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
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name, rate=100)
        self.test_pos.append(po.name)
        po.submit()
        
        # Crear batch con vencimiento corto (2 meses, bajo umbral de 6)
        batch_corto = create_test_batch(item.name, f"BATCH-CORTO-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch_corto.batch_id)
        
        # Crear Purchase Receipt con item que tiene vencimiento corto
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
        
        # Validar que el método validate_umbral_vencimiento se ejecuta
        pr.validate()
        
        # Validar que el item quedó en Cuarentena automáticamente
        self.assertEqual(pr.items[0].custom_qc_status, "Cuarentena", "Item con vencimiento corto debe quedar en Cuarentena automáticamente")
        self.assertEqual(pr.items[0].custom_qc_rejection_reason, "Vencimiento corto", "Debe tener causa de cuarentena")
        
        self.test_prs.append(pr.name)
    
    def test_invariante_umbral_vencimiento_no_sobrescribe_rechazo_manual(self):
        """
        Invariante DDD: Si un item ya está rechazado manualmente, no se sobrescribe a Cuarentena
        """
        # Setup
        company_name = get_test_company()
        
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
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company_name)
        self.test_warehouses.append(warehouse.name)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name, rate=100)
        self.test_pos.append(po.name)
        po.submit()
        
        # Crear batch con vencimiento corto (2 meses)
        batch_corto = create_test_batch(item.name, f"BATCH-CORTO-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch_corto.batch_id)
        
        # Crear Purchase Receipt con item rechazado manualmente
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
                    "custom_qc_status": "Rechazado",  # Rechazado manualmente
                    "custom_qc_rejection_reason": "Empaque dañado",
                }
            ]
        })
        pr.insert(ignore_permissions=True)
        
        # Validar que el método validate_umbral_vencimiento se ejecuta
        pr.validate()
        
        # Validar que el estado Rechazado NO se sobrescribe
        self.assertEqual(pr.items[0].custom_qc_status, "Rechazado", "Item rechazado manualmente NO debe cambiar a Cuarentena")
        self.assertEqual(pr.items[0].custom_qc_rejection_reason, "Empaque dañado", "La causa manual debe mantenerse")
        
        self.test_prs.append(pr.name)
    
    def test_invariante_umbral_vencimiento_respetado_por_item_group(self):
        """
        Invariante DDD: El umbral configurado en Item Group tiene prioridad sobre Company
        """
        # Setup
        company_name = get_test_company()
        
        # Configurar Company con umbral de 12 meses
        frappe.db.set_value("Company", company_name, "custom_minimum_expiry_months", 12)
        frappe.db.commit()
        
        # Crear Item Group con umbral más estricto de 3 meses
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": f"TEST-IG-{frappe.generate_hash(length=6)}",
            "is_group": 0,
        })
        item_group.insert(ignore_permissions=True)
        frappe.db.commit()
        # Configurar umbral después de insertar (para asegurar que se guarde)
        frappe.db.set_value("Item Group", item_group.name, "custom_minimum_expiry_months", 3)
        frappe.db.commit()
        item_group.reload()
        self.test_item_groups.append(item_group.name)
        
        # Verificar que el umbral se guardó correctamente
        self.assertEqual(item_group.get("custom_minimum_expiry_months"), 3, "Item Group debe tener umbral de 3 meses")
        
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
        
        # Verificar que el item tiene el item_group correcto
        self.assertEqual(item.item_group, item_group.name, f"Item debe tener item_group {item_group.name}, pero tiene {item.item_group}")
        
        # Verificar que el Item Group del item tiene el umbral correcto
        item_group_del_item = frappe.get_doc("Item Group", item.item_group)
        self.assertEqual(item_group_del_item.get("custom_minimum_expiry_months"), 3, f"Item Group del item debe tener umbral de 3 meses, pero tiene {item_group_del_item.get('custom_minimum_expiry_months')}")
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company_name)
        self.test_warehouses.append(warehouse.name)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name, rate=100)
        self.test_pos.append(po.name)
        po.submit()
        
        # Crear batch con vencimiento de 4 meses (bajo umbral de Company 12, pero bajo umbral de Item Group 3)
        batch_4meses = create_test_batch(item.name, f"BATCH-4M-{frappe.generate_hash(length=6)}", add_months(today(), 4))
        self.test_batches.append(batch_4meses.batch_id)
        
        # Crear Purchase Receipt (sin umbral propio)
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
                    "batch_no": batch_4meses.batch_id,
                    "custom_qc_status": "Aceptado",
                }
            ]
        })
        pr.insert(ignore_permissions=True)
        
        # Verificar umbral obtenido antes de validar
        # Recargar el Item Group para asegurar que tiene el umbral correcto
        item_group.reload()
        self.assertEqual(item_group.get("custom_minimum_expiry_months"), 3, f"Item Group debe tener umbral de 3 meses, pero tiene {item_group.get('custom_minimum_expiry_months')}")
        
        # Recargar el item para asegurar que tiene el item_group correcto
        item.reload()
        self.assertEqual(item.item_group, item_group.name, f"Item debe tener item_group {item_group.name}, pero tiene {item.item_group}")
        
        # Obtener umbral - debe usar Item Group (3) en lugar de PR default (6) o Company (12)
        threshold_obtenido = pr.get_minimum_expiry_months(item.name)
        self.assertEqual(threshold_obtenido, 3, f"Debe obtener umbral de 3 meses desde Item Group, pero obtuvo {threshold_obtenido}. PR tiene {pr.get('custom_minimum_expiry_months')}, Company tiene {frappe.db.get_value('Company', company_name, 'custom_minimum_expiry_months')}, Item Group tiene {frappe.db.get_value('Item Group', item_group.name, 'custom_minimum_expiry_months')}")
        
        # Validar
        pr.validate()
        
        # Validar que se aplica el umbral del Item Group (3 meses), no el de Company (12 meses)
        # 4 meses >= 3 meses, así que NO debe quedar en Cuarentena (solo si es < 3)
        self.assertEqual(pr.items[0].custom_qc_status, "Aceptado", f"Item con 4 meses de vencimiento NO debe quedar en Cuarentena si el umbral es 3 meses. Estado actual: {pr.items[0].custom_qc_status}")
        
        # Ahora probar con batch de 2 meses (bajo umbral de Item Group)
        batch_2meses = create_test_batch(item.name, f"BATCH-2M-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch_2meses.batch_id)
        
        pr2 = frappe.get_doc({
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
                    "batch_no": batch_2meses.batch_id,
                    "custom_qc_status": "Aceptado",
                }
            ]
        })
        pr2.insert(ignore_permissions=True)
        pr2.validate()
        
        # Validar que 2 meses < 3 meses, así que SÍ debe quedar en Cuarentena
        self.assertEqual(pr2.items[0].custom_qc_status, "Cuarentena", "Item con 2 meses de vencimiento debe quedar en Cuarentena si el umbral es 3 meses")
        
        self.test_prs.extend([pr.name, pr2.name])

