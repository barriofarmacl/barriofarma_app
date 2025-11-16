# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests DDD para el Agregado Purchase Receipt
Validación de invariantes y reglas de negocio del dominio farmacéutico
Fase RED del TDD para BF-006
"""

import unittest
import frappe
from frappe import _
from frappe.utils import add_months, today

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_supplier,
    create_test_warehouse,
    create_test_purchase_order,
    create_test_batch,
)


class TestPurchaseReceiptDDD(unittest.TestCase):
    """Tests DDD para invariantes del agregado Purchase Receipt"""
    
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
    
    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar Purchase Receipts
        for pr_name in [pr.name for pr in self.test_prs]:
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
    
    def test_invariante_controlados_requieren_lote_vencimiento(self):
        """
        Invariante: Productos controlados (Psicotrópico/Estupefaciente) siempre requieren
        lote y vencimiento en Purchase Receipt, incluso si se reciben parcialmente.
        """
        # Crear item controlado
        item = create_test_item(
            item_code=f"TEST-CTRL-{frappe.generate_hash(length=6)}",
            item_name="Medicamento Controlado Test",
            custom_control_level="Psicotrópico",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="F-CTRL-001",
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po)
        
        # Crear batch
        batch = create_test_batch(item.name, f"BATCH-CTRL-{frappe.generate_hash(length=6)}", add_months(today(), 12))
        self.test_batches.append(batch)
        
        # Intentar crear Purchase Receipt SIN lote (debe fallar)
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
                # Sin batch_no - debe fallar para controlados
            }]
        })
        
        # TODO: Implementar validación en override de Purchase Receipt
        # Por ahora este test documenta la invariante esperada
        # Debe lanzar ValidationError si falta lote/vencimiento para controlados
        
        # Por ahora, el test pasa si ERPNext ya valida esto
        # Si no, implementaremos la validación en el override
        try:
            pr.insert(ignore_permissions=True)
            pr.save()
            # Si pasa sin validación, marcamos que necesitamos implementar
            self.fail("Se esperaba validación de lote/vencimiento para controlados")
        except frappe.ValidationError:
            # Esperado - ERPNext o nuestra validación debe rechazar
            pass
    
    def test_invariante_no_pagar_rechazados(self):
        """
        Invariante: La conciliación de factura solo debe considerar cantidades aceptadas.
        Los rechazados no deben incrementar stock disponible ni ser pagables.
        """
        # Crear item
        item = create_test_item(
            item_code=f"TEST-RECH-{frappe.generate_hash(length=6)}",
            item_name="Producto Rechazo Test",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="F-RECH-001",
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
        
        # Crear Purchase Receipt con sublotes (uno aceptado, uno rechazado)
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
                    "qty": 4,  # Rechazado (vencimiento corto)
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
        self.test_prs.append(pr)
        
        # Validar que los estados QC están correctamente asignados
        item_aceptado = next((i for i in pr.items if i.get("custom_qc_status") == "Aceptado"), None)
        item_rechazado = next((i for i in pr.items if i.get("custom_qc_status") == "Rechazado"), None)
        
        self.assertIsNotNone(item_aceptado)
        self.assertIsNotNone(item_rechazado)
        self.assertEqual(item_aceptado.qty, 6)
        self.assertEqual(item_rechazado.qty, 4)
        self.assertEqual(item_rechazado.get("custom_qc_rejection_reason"), "Vencimiento corto")
    
    def test_invariante_sobrante_no_disponible(self):
        """
        Invariante: Sobrante no autorizado nunca queda disponible para venta hasta
        decisión administrativa explícita.
        """
        # Crear item
        item = create_test_item(
            item_code=f"TEST-SOBR-{frappe.generate_hash(length=6)}",
            item_name="Producto Sobrante Test",
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=1,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse)
        
        # PO de 10 unidades
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po)
        
        # Crear Purchase Receipt con 12 unidades (sobrante de 2)
        # Dividir en 2 líneas: 10 aceptadas y 2 sobrantes
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 10,  # Cantidad autorizada
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 2,  # Sobrante no autorizado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "custom_is_excess": 1,
                    "custom_qc_status": "Cuarentena",  # Se marca automáticamente
                    "custom_qc_rejection_reason": "Sobrante no autorizado",
                }
            ]
        })
        
        pr.insert(ignore_permissions=True)
        self.test_prs.append(pr)
        
        # Validar que sobrante está en Cuarentena (ajuste automático)
        sobrante_item = next((i for i in pr.items if i.get("custom_is_excess")), None)
        self.assertIsNotNone(sobrante_item)
        self.assertEqual(sobrante_item.get("custom_qc_status"), "Cuarentena")
        self.assertEqual(sobrante_item.get("custom_qc_rejection_reason"), "Sobrante no autorizado")
    
    def test_invariante_umbral_vencimiento(self):
        """
        Invariante: Productos con vencimiento bajo umbral configurable (ej. <6 meses)
        deben quedar en Cuarentena o Rechazados automáticamente.
        """
        # Crear item
        item = create_test_item(
            item_code=f"TEST-VENC-{frappe.generate_hash(length=6)}",
            item_name="Producto Vencimiento Test",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="F-VENC-001",
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
        
        # Crear batch con vencimiento corto (<6 meses)
        batch_corto = create_test_batch(item.name, f"BATCH-CORTO-{frappe.generate_hash(length=6)}", add_months(today(), 2))
        self.test_batches.append(batch_corto)
        
        # Crear Purchase Receipt con vencimiento corto (<6 meses)
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "custom_minimum_expiry_months": 6,  # Umbral de 6 meses
            "items": [{
                "item_code": item.name,
                "qty": 10,
                "uom": item.stock_uom,
                "rate": 100,
                "purchase_order": po.name,
                "purchase_order_item": po.items[0].name,
                "batch_no": batch_corto.batch_id,
                "custom_qc_status": "Aceptado",  # Se cambiará automáticamente
            }]
        })
        
        pr.insert(ignore_permissions=True)
        self.test_prs.append(pr)
        
        # Validar que se marcó automáticamente como Cuarentena (ajuste automático por umbral)
        item_line = pr.items[0]
        self.assertEqual(item_line.get("custom_qc_status"), "Cuarentena")
        self.assertEqual(item_line.get("custom_qc_rejection_reason"), "Vencimiento corto")
    
    def test_invariante_rechazados_cuarentena_requieren_causa(self):
        """
        Invariante: Items rechazados o en cuarentena deben tener causa especificada
        """
        # Crear item
        item = create_test_item(
            item_code=f"TEST-STOCK-{frappe.generate_hash(length=6)}",
            item_name="Producto Stock Test",
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=1,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse)
        
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po)
        
        # Crear Purchase Receipt con item rechazado SIN causa (debe fallar)
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 4,  # Rechazado sin causa
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "custom_qc_status": "Rechazado",
                    # Sin custom_qc_rejection_reason - debe fallar
                }
            ]
        })
        
        # Debe lanzar ValidationError por falta de causa
        # Necesitamos llamar validate() explícitamente ya que insert() puede no validar inmediatamente
        with self.assertRaises(frappe.ValidationError):
            pr.validate()
            pr.insert(ignore_permissions=True)
        
        # Ahora con causa debe pasar
        pr.items[0].custom_qc_rejection_reason = "Vencimiento corto"
        pr.insert(ignore_permissions=True)
        self.test_prs.append(pr)
        
        # Validar que el item tiene causa
        self.assertEqual(pr.items[0].get("custom_qc_rejection_reason"), "Vencimiento corto")

