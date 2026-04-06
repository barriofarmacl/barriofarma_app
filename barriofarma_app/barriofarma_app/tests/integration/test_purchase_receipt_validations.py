# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests Unitarios para Validaciones DDD de Purchase Receipt
Story 9.1: Tests Unitarios para Validaciones DDD

Cubre las validaciones en barriofarma_app/overrides/purchase_receipt.py:
- validate_against_purchase_order
- auto_create_batches_if_needed
- validate_items_requieren_lote_si_necesario
- validate_controlados_requieren_lote_vencimiento
- validate_qc_rejection_reason_required
- validate_umbral_vencimiento
- validate_sobrante_no_disponible
- make_purchase_invoice (método de conciliación)
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_months, today, add_days

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_supplier,
    create_test_warehouse,
    create_test_purchase_order,
    create_test_batch,
    get_test_company,
)
from barriofarma_app.barriofarma_app.overrides.purchase_receipt import make_purchase_invoice


class TestPurchaseReceiptValidations(FrappeTestCase):
    """Tests unitarios para validaciones DDD de Purchase Receipt"""
    
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
        self.test_item_groups = []
    
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
    
    # ========================================
    # TESTS: validate_against_purchase_order
    # ========================================
    
    def test_purchase_receipt_without_po_should_pass(self):
        """
        Validación: Purchase Receipt sin PO debe pasar (compra directa)
        """
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear Purchase Receipt sin PO
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": get_test_company(),
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "uom": item.stock_uom,
                "rate": 100,
            }]
        })
        
        # No debe lanzar error
        pr.insert(ignore_permissions=True)
        self.test_prs.append(pr.name)
        self.assertIsNotNone(pr.name, "Purchase Receipt sin PO debe crearse correctamente")
    
    # ========================================
    # TESTS: validate_items_requieren_lote_si_necesario
    # ========================================
    
    def test_item_with_batch_no_requires_batch_in_pr(self):
        """
        Validación: Item con has_batch_no=1 requiere batch_no en Purchase Receipt
        """
        item = create_test_item(
            item_code=f"TEST-BATCH-{frappe.generate_hash(length=6)}",
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
        
        # Intentar crear Purchase Receipt sin batch_no (debe fallar)
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": get_test_company(),
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "uom": item.stock_uom,
                "rate": 100,
                # Sin batch_no
            }]
        })
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError) as context:
            pr.insert(ignore_permissions=True)
            pr.submit()
        
        error_msg = str(context.exception)
        self.assertIn("lote", error_msg.lower(), "Debe lanzar error sobre lote faltante")
    
    # ========================================
    # TESTS: validate_controlados_requieren_lote_vencimiento
    # ========================================
    
    def test_controlled_item_requires_batch_and_expiry(self):
        """
        Validación: Producto controlado (Psicotrópico/Estupefaciente) requiere lote y vencimiento
        """
        item = create_test_item(
            item_code=f"TEST-CTRL-{frappe.generate_hash(length=6)}",
            custom_control_level="Psicotrópico",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="F-CTRL-001",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po.name)
        
        # Crear batch con vencimiento
        batch = create_test_batch(item.name, f"BATCH-CTRL-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        self.test_batches.append(batch.batch_id)
        
        # Intentar crear Purchase Receipt sin batch (debe fallar)
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
                # Sin batch_no
            }]
        })
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError):
            pr.insert(ignore_permissions=True)
            pr.submit()
    
    def test_controlled_item_with_batch_and_expiry_should_pass(self):
        """
        Validación: Producto controlado CON lote y vencimiento debe pasar
        """
        item = create_test_item(
            item_code=f"TEST-CTRL-OK-{frappe.generate_hash(length=6)}",
            custom_control_level="Estupefaciente",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="F-CTRL-002",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po.name)
        
        batch = create_test_batch(item.name, f"BATCH-OK-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        self.test_batches.append(batch.batch_id)
        
        # Crear Purchase Receipt con batch y vencimiento
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
                "batch_no": batch.batch_id,
            }]
        })
        
        # No debe lanzar error
        pr.insert(ignore_permissions=True)
        self.test_prs.append(pr.name)
        self.assertIsNotNone(pr.name, "Purchase Receipt de controlado con lote debe crearse")
    
    # ========================================
    # TESTS: validate_qc_rejection_reason_required
    # ========================================
    
    def test_rejected_item_requires_rejection_reason(self):
        """
        Validación: Item con custom_qc_status='Rechazado' requiere custom_qc_rejection_reason
        """
        item = create_test_item(
            item_code=f"TEST-REJECT-{frappe.generate_hash(length=6)}",
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
        
        batch = create_test_batch(item.name, f"BATCH-REJECT-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch.batch_id)
        
        # Intentar crear Purchase Receipt con item rechazado sin causa
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": get_test_company(),
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "uom": item.stock_uom,
                "rate": 100,
                "batch_no": batch.batch_id,
                "custom_qc_status": "Rechazado",
                # Sin custom_qc_rejection_reason
            }]
        })
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError) as context:
            pr.insert(ignore_permissions=True)
        
        error_msg = str(context.exception)
        self.assertIn("rechazo", error_msg.lower(), "Debe exigir razón de rechazo")
    
    def test_quarantine_item_requires_rejection_reason(self):
        """
        Validación: Item con custom_qc_status='Cuarentena' requiere custom_qc_rejection_reason
        """
        item = create_test_item(
            item_code=f"TEST-QUAR-{frappe.generate_hash(length=6)}",
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
        
        batch = create_test_batch(item.name, f"BATCH-QUAR-{frappe.generate_hash(length=6)}", add_months(today(), 10))
        self.test_batches.append(batch.batch_id)
        
        # Intentar crear Purchase Receipt con item en cuarentena sin causa
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": get_test_company(),
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "uom": item.stock_uom,
                "rate": 100,
                "batch_no": batch.batch_id,
                "custom_qc_status": "Cuarentena",
                # Sin custom_qc_rejection_reason
            }]
        })
        
        # Debe lanzar ValidationError
        with self.assertRaises(frappe.ValidationError) as context:
            pr.insert(ignore_permissions=True)
        
        error_msg = str(context.exception)
        self.assertIn("cuarentena", error_msg.lower(), "Debe exigir razón de cuarentena")
    
    def test_accepted_item_does_not_require_rejection_reason(self):
        """
        Validación: Item con custom_qc_status='Aceptado' NO requiere custom_qc_rejection_reason
        """
        item = create_test_item(
            item_code=f"TEST-ACCEPT-{frappe.generate_hash(length=6)}",
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
        
        batch = create_test_batch(item.name, f"BATCH-ACCEPT-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        self.test_batches.append(batch.batch_id)
        
        # Crear Purchase Receipt con item aceptado sin causa
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": get_test_company(),
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "uom": item.stock_uom,
                "rate": 100,
                "batch_no": batch.batch_id,
                "custom_qc_status": "Aceptado",
                # Sin custom_qc_rejection_reason (válido para Aceptado)
            }]
        })
        
        # No debe lanzar error
        pr.insert(ignore_permissions=True)
        self.test_prs.append(pr.name)
        self.assertIsNotNone(pr.name, "Item aceptado no debe exigir razón de rechazo")
    
    # ========================================
    # TESTS: validate_umbral_vencimiento
    # ========================================
    
    def test_expiry_threshold_auto_quarantine(self):
        """
        Validación: Item con vencimiento bajo umbral queda en Cuarentena automáticamente
        """
        company_name = get_test_company()
        
        # Crear Item Group con umbral de 6 meses
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": f"TEST-IG-{frappe.generate_hash(length=6)}",
            "is_group": 0,
        })
        item_group.insert(ignore_permissions=True)
        frappe.db.set_value("Item Group", item_group.name, "custom_minimum_expiry_months", 6)
        frappe.db.commit()
        item_group.reload()
        self.test_item_groups.append(item_group.name)
        
        item = create_test_item(
            item_code=f"TEST-EXPIRY-{frappe.generate_hash(length=6)}",
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
        
        # Batch con vencimiento corto (2 meses < 6 meses del umbral)
        batch = create_test_batch(item.name, f"BATCH-SHORT-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch.batch_id)
        
        # Crear Purchase Receipt
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": company_name,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "uom": item.stock_uom,
                "rate": 100,
                "purchase_order": po.name,
                "purchase_order_item": po.items[0].name,
                "batch_no": batch.batch_id,
                "custom_qc_status": "Aceptado",  # Inicialmente aceptado
            }]
        })
        pr.insert(ignore_permissions=True)
        pr.validate()  # Trigger validate_umbral_vencimiento
        
        # Validar que cambió a Cuarentena automáticamente
        self.assertEqual(pr.items[0].custom_qc_status, "Cuarentena", "Debe cambiar a Cuarentena por vencimiento corto")
        self.assertEqual(pr.items[0].custom_qc_rejection_reason, "Vencimiento corto", "Debe tener causa automática")
        self.test_prs.append(pr.name)
    
    def test_expiry_threshold_does_not_overwrite_manual_rejection(self):
        """
        Validación: Umbral de vencimiento NO sobrescribe rechazo manual
        """
        item = create_test_item(
            item_code=f"TEST-MANUAL-{frappe.generate_hash(length=6)}",
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
        
        batch = create_test_batch(item.name, f"BATCH-MANUAL-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch.batch_id)
        
        # Crear Purchase Receipt con rechazo manual
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
                "batch_no": batch.batch_id,
                "custom_qc_status": "Rechazado",  # Rechazado manualmente
                "custom_qc_rejection_reason": "Empaque dañado",
            }]
        })
        pr.insert(ignore_permissions=True)
        pr.validate()
        
        # Validar que NO cambió
        self.assertEqual(pr.items[0].custom_qc_status, "Rechazado", "Estado manual no debe cambiar")
        self.assertEqual(pr.items[0].custom_qc_rejection_reason, "Empaque dañado", "Causa manual debe mantenerse")
        self.test_prs.append(pr.name)
    
    # ========================================
    # TESTS: validate_sobrante_no_disponible
    # ========================================
    
    def test_excess_item_marked_with_is_excess_flag(self):
        """
        Validación: Sobrante no autorizado se marca con custom_is_excess=1
        """
        item = create_test_item(
            item_code=f"TEST-EXCESS-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # PO de 10 unidades
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po.name)
        po.submit()
        
        # Recepción de 15 unidades (5 de sobrante)
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [{
                "item_code": item.name,
                "qty": 15,  # Sobrante de 5
                "uom": item.stock_uom,
                "rate": 100,
                "purchase_order": po.name,
                "purchase_order_item": po.items[0].name,
            }]
        })
        pr.insert(ignore_permissions=True)
        pr.validate()
        
        # Validar que se marcó como sobrante
        self.assertEqual(pr.items[0].custom_is_excess, 1, "Debe marcar sobrante con custom_is_excess=1")
        self.test_prs.append(pr.name)
    
    # ========================================
    # TESTS: make_purchase_invoice (Conciliación)
    # ========================================
    
    def test_invoice_excludes_rejected_items(self):
        """
        Validación: Purchase Invoice NO debe incluir items rechazados
        Si todos los items están rechazados, debe lanzar error al intentar insertar (sin items)
        """
        item = create_test_item(
            item_code=f"TEST-INV-REJ-{frappe.generate_hash(length=6)}",
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
        
        batch = create_test_batch(item.name, f"BATCH-REJ-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch.batch_id)
        
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
                "batch_no": batch.batch_id,
                "custom_qc_status": "Rechazado",
                "custom_qc_rejection_reason": "Vencimiento corto",
            }]
        })
        pr.insert(ignore_permissions=True)
        pr.submit()
        self.test_prs.append(pr.name)
        
        # Intentar crear Purchase Invoice: debe lanzar error porque todos los items están rechazados
        # La función make_purchase_invoice valida esto en set_missing_values
        try:
            pi = make_purchase_invoice(pr.name)
            # Si no lanza error en make_purchase_invoice, debe fallar al insertar (0 items)
            with self.assertRaises((frappe.ValidationError, frappe.exceptions.MandatoryError)):
                pi.insert(ignore_permissions=True)
        except frappe.ValidationError as e:
            # Si lanza error directamente en make_purchase_invoice, verificar que menciona "Rechazados"
            self.assertIn("Rechazados", str(e), "Debe indicar que los items están rechazados")
    
    def test_invoice_excludes_quarantine_items(self):
        """
        Validación: Purchase Invoice NO debe incluir items en cuarentena
        Si todos los items están en cuarentena, debe lanzar error al intentar insertar (sin items)
        """
        item = create_test_item(
            item_code=f"TEST-INV-QUAR-{frappe.generate_hash(length=6)}",
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
        
        batch = create_test_batch(item.name, f"BATCH-QUAR-{frappe.generate_hash(length=6)}", add_months(today(), 10))
        self.test_batches.append(batch.batch_id)
        
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
                "batch_no": batch.batch_id,
                "custom_qc_status": "Cuarentena",
                "custom_qc_rejection_reason": "Sin evidencia de cadena de frío",
            }]
        })
        pr.insert(ignore_permissions=True)
        pr.submit()
        self.test_prs.append(pr.name)
        
        # Intentar crear Purchase Invoice: debe lanzar error porque todos los items están en cuarentena
        # La función make_purchase_invoice valida esto en set_missing_values
        try:
            pi = make_purchase_invoice(pr.name)
            # Si no lanza error en make_purchase_invoice, debe fallar al insertar (0 items)
            with self.assertRaises((frappe.ValidationError, frappe.exceptions.MandatoryError)):
                pi.insert(ignore_permissions=True)
        except frappe.ValidationError as e:
            # Si lanza error directamente en make_purchase_invoice, verificar que menciona "Cuarentena"
            self.assertIn("Cuarentena", str(e), "Debe indicar que los items están en cuarentena")
    
    def test_invoice_includes_only_accepted_items(self):
        """
        Validación: Purchase Invoice SOLO debe incluir items aceptados (filtra automáticamente rechazados)
        """
        item = create_test_item(
            item_code=f"TEST-INV-MIX-{frappe.generate_hash(length=6)}",
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
        
        batch_accepted = create_test_batch(item.name, f"BATCH-ACC-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        batch_rejected = create_test_batch(item.name, f"BATCH-REJ-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.extend([batch_accepted.batch_id, batch_rejected.batch_id])
        
        # Crear Purchase Receipt con items mixtos (dos rows separados para cada batch)
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
                    "batch_no": batch_accepted.batch_id,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 8,  # Rechazado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_rejected.batch_id,
                    "custom_qc_status": "Rechazado",
                    "custom_qc_rejection_reason": "Vencimiento corto",
                }
            ]
        })
        pr.insert(ignore_permissions=True)
        pr.submit()
        self.test_prs.append(pr.name)
        
        # Crear Purchase Invoice (debe filtrar automáticamente el item rechazado)
        pi = make_purchase_invoice(pr.name)
        pi.insert(ignore_permissions=True)
        self.test_pis.append(pi.name)
        
        # Validar que SOLO incluye aceptados (filtrado automático)
        self.assertEqual(len(pi.items), 1, "Debe tener solo 1 item (el aceptado, filtrado automáticamente)")
        self.assertEqual(pi.items[0].qty, 12, "Debe incluir solo la cantidad aceptada")
        total_esperado = 12 * 100
        self.assertEqual(pi.total, total_esperado, f"Total debe ser {total_esperado} (solo aceptados)")
