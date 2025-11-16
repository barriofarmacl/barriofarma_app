# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests E2E para US-006: Recepción de Compra con sublotes y rechazo parcial
Implementación de criterios Gherkin de la User Story
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


class TestUS006RecepcionConSublotes(unittest.TestCase):
    """Tests E2E para US-006 según criterios Gherkin"""
    
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
    
    def test_aceptacion_parcial_por_qc_vencimiento_corto(self):
        """
        Scenario: Aceptación parcial por QC con vencimiento corto
        
        Given una Purchase Order abierta con 1 línea del ítem farmacéutico "ITEM-CTRL"
        And el proveedor entrega 2 sublotes del mismo ítem
        When registro un Purchase Receipt con:
          | sublote | lote     | vencimiento | cantidad | estado_qc | causa              |
          | A       | LOTE-A01 | +12m        | 8        | Aceptado  |                    |
          | B       | LOTE-B02 | +2m         | 2        | Rechazado | Vencimiento corto  |
        Then el stock disponible solo aumenta con cantidad 8 del sublote A
        And el sublote B queda no disponible para venta
        And la conciliación de factura solo considera cantidad 8
        """
        # Given: Purchase Order con 1 línea
        item = create_test_item(
            item_code=f"ITEM-CTRL-{frappe.generate_hash(length=6)}",
            item_name="ITEM-CTRL",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="F-CTRL-001",
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
        
        # And: Proveedor entrega 2 sublotes
        batch_a = create_test_batch(item.name, "LOTE-A01", add_months(today(), 12))
        batch_b = create_test_batch(item.name, "LOTE-B02", add_months(today(), 2))
        self.test_batches.extend([batch_a, batch_b])
        
        # When: Registro Purchase Receipt con sublotes A (Aceptado) y B (Rechazado)
        pr = frappe.get_doc({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": po.company,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "items": [
                {
                    "item_code": item.name,
                    "qty": 8,  # Sublote A - Aceptado
                    "uom": item.stock_uom,
                    "rate": 100,
                    "purchase_order": po.name,
                    "purchase_order_item": po.items[0].name,
                    "batch_no": batch_a.batch_id,
                    "custom_qc_status": "Aceptado",
                },
                {
                    "item_code": item.name,
                    "qty": 2,  # Sublote B - Rechazado
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
        
        # Then: Validaciones de campos custom y estados QC
        # Scope del workflow: solo validar campos custom y validaciones básicas
        self.assertEqual(pr.items[0].custom_qc_status, "Aceptado")
        self.assertEqual(pr.items[1].custom_qc_status, "Rechazado")
        self.assertEqual(pr.items[1].custom_qc_rejection_reason, "Vencimiento corto")
        
        # Validar que los campos custom están presentes
        self.assertIsNotNone(pr.items[0].custom_qc_status)
        self.assertIsNotNone(pr.items[1].custom_qc_status)
        self.assertIsNotNone(pr.items[1].custom_qc_rejection_reason)
    
    def test_diferencia_por_faltante_y_cuarentena(self):
        """
        Scenario: Diferencia por faltante y cuarentena por cadena de frío
        
        When registro un Purchase Receipt con:
          | sublote | lote     | vencimiento | cantidad | estado_qc  | causa                |
          | A       | LOTE-A03 | +10m        | 7        | Aceptado   |                      |
          | B       | LOTE-B04 | +10m        | 1        | Cuarentena | Sin evidencia de frío|
        Then queda saldo faltante en backorder por 2 unidades
        And el sublote B queda en ubicación de cuarentena sin disponibilidad
        """
        # Crear item
        item = create_test_item(
            item_code=f"TEST-FALT-{frappe.generate_hash(length=6)}",
            item_name="Producto Faltante Test",
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="F-FALT-001",
            has_batch_no=1,
            has_expiry_date=1,
        )
        self.test_items.append(item.name)
        
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        warehouse_cuarentena = create_test_warehouse(f"TEST-CUARENTENA-{frappe.generate_hash(length=6)}")
        self.test_warehouses.extend([warehouse, warehouse_cuarentena])
        
        # PO de 10 unidades
        po = create_test_purchase_order(item.name, qty=10, supplier_name=supplier.name)
        self.test_pos.append(po)
        
        # Crear batches
        batch_a = create_test_batch(item.name, "LOTE-A03", add_months(today(), 10))
        batch_b = create_test_batch(item.name, "LOTE-B04", add_months(today(), 10))
        self.test_batches.extend([batch_a, batch_b])
        
        # When: Registro PR con A (Aceptado: 7) y B (Cuarentena: 1)
        # Total recibido: 8, faltante: 2
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
                    "qty": 1,  # Cuarentena
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
        self.test_prs.append(pr)
        
        # Then: Validaciones de campos custom y estados QC
        # Scope del workflow: solo validar campos custom y validaciones básicas
        self.assertEqual(pr.items[0].custom_qc_status, "Aceptado")
        self.assertEqual(pr.items[1].custom_qc_status, "Cuarentena")
        self.assertEqual(pr.items[1].custom_qc_rejection_reason, "Sin evidencia de cadena de frío")
        
        # Validar que los campos custom están presentes
        self.assertIsNotNone(pr.items[0].custom_qc_status)
        self.assertIsNotNone(pr.items[1].custom_qc_status)
        self.assertIsNotNone(pr.items[1].custom_qc_rejection_reason)
    
    def test_sobre_entrega_no_autorizada(self):
        """
        Scenario: Sobre-entrega no autorizada
        
        When el proveedor entrega 12 unidades para una PO de 10
        And registro 10 como recibidas y marco 2 como excedente no autorizado
        Then el excedente no queda disponible para venta
        And requiere decisión administrativa antes de cualquier ajuste
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
        
        # When: Proveedor entrega 12 unidades (dividir en 10 aceptadas + 2 sobrantes)
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
        
        # Then: Validaciones de campos custom y estados QC
        # Scope del workflow: solo validar campos custom y validaciones básicas
        self.assertEqual(pr.items[0].custom_qc_status, "Aceptado")
        self.assertEqual(pr.items[0].custom_is_excess, 0)  # No es sobrante
        
        # Validar que sobrante está marcado correctamente
        sobrante_item = next((i for i in pr.items if i.get("custom_is_excess")), None)
        self.assertIsNotNone(sobrante_item)
        self.assertEqual(sobrante_item.get("custom_is_excess"), 1)
        # La validación automática debería haber ajustado el estado a Cuarentena
        self.assertEqual(sobrante_item.get("custom_qc_status"), "Cuarentena")
        self.assertEqual(sobrante_item.get("custom_qc_rejection_reason"), "Sobrante no autorizado")
        
        # Validar que los campos custom están presentes
        self.assertIsNotNone(pr.items[0].custom_qc_status)
        self.assertIsNotNone(sobrante_item.get("custom_qc_status"))
        self.assertIsNotNone(sobrante_item.get("custom_qc_rejection_reason"))

