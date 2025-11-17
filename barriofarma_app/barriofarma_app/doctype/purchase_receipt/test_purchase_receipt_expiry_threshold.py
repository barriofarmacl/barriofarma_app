# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para BF-008: Política de umbral de vencimiento configurable
Validar evaluación de fechas vs umbral y obtención de umbral desde Company/Item Group
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
)
from barriofarma_app.barriofarma_app.overrides.purchase_receipt import PurchaseReceipt


class TestPurchaseReceiptExpiryThreshold(unittest.TestCase):
    """Tests unitarios para umbral de vencimiento configurable"""
    
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
        self.test_companies = []
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
        
        # Limpiar Companies (solo si las creamos)
        for company_name in self.test_companies:
            try:
                frappe.delete_doc("Company", company_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()
    
    def test_get_minimum_expiry_months_from_company(self):
        """
        Test: Obtener umbral desde Company cuando está configurado
        """
        # Setup: Usar Company existente o crear una básica
        company_name = frappe.db.get_value("Company", {"name": ("!=", "")}, "name")
        if not company_name:
            # Crear Company básica si no existe
            company = frappe.get_doc({
                "doctype": "Company",
                "company_name": f"TEST-COMPANY-{frappe.generate_hash(length=6)}",
                "abbr": "TC",
                "default_currency": "USD",
            })
            company.insert(ignore_permissions=True)
            frappe.db.commit()
            company_name = company.name
            self.test_companies.append(company_name)
        
        # Configurar umbral en Company existente
        frappe.db.set_value("Company", company_name, "custom_minimum_expiry_months", 12)
        frappe.db.commit()
        
        # Crear Purchase Receipt sin umbral propio
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company_name)
        self.test_warehouses.append(warehouse.name)
        
        pr = PurchaseReceipt({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": company_name,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
        })
        
        # Validar que obtiene umbral desde Company
        threshold = pr.get_minimum_expiry_months()
        self.assertEqual(threshold, 12, "Debe obtener umbral de 12 meses desde Company")
    
    def test_get_minimum_expiry_months_from_item_group(self):
        """
        Test: Obtener umbral desde Item Group cuando está configurado (prioridad sobre Company)
        """
        # Setup: Usar Company existente o crear una básica
        company_name = frappe.db.get_value("Company", {"name": ("!=", "")}, "name")
        if not company_name:
            company = frappe.get_doc({
                "doctype": "Company",
                "company_name": f"TEST-COMPANY-{frappe.generate_hash(length=6)}",
                "abbr": "TC",
                "default_currency": "USD",
            })
            company.insert(ignore_permissions=True)
            frappe.db.commit()
            company_name = company.name
            self.test_companies.append(company_name)
        
        # Configurar umbral en Company existente
        frappe.db.set_value("Company", company_name, "custom_minimum_expiry_months", 6)
        frappe.db.commit()
        
        # Crear Item Group con umbral de 9 meses
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": f"TEST-IG-{frappe.generate_hash(length=6)}",
            "is_group": 0,
            "custom_minimum_expiry_months": 9,
        })
        item_group.insert(ignore_permissions=True)
        frappe.db.commit()
        self.test_item_groups.append(item_group.name)
        
        # Crear Item en ese Item Group
        item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre",
            item_group=item_group.name,
        )
        self.test_items.append(item.name)
        
        # Crear Purchase Receipt
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company_name)
        self.test_warehouses.append(warehouse.name)
        
        pr = PurchaseReceipt({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": company_name,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
        })
        
        # Validar que obtiene umbral desde Item Group (prioridad sobre Company)
        threshold = pr.get_minimum_expiry_months(item.name)
        self.assertEqual(threshold, 9, "Debe obtener umbral de 9 meses desde Item Group (prioridad sobre Company)")
    
    def test_get_minimum_expiry_months_fallback(self):
        """
        Test: Fallback a valor por defecto (6 meses) cuando Company usa el default
        Nota: Company siempre tiene default de 6 meses, así que este test verifica que se respeta
        """
        # Setup: Usar Company existente
        company_name = frappe.db.get_value("Company", {"name": ("!=", "")}, "name")
        if not company_name:
            company = frappe.get_doc({
                "doctype": "Company",
                "company_name": f"TEST-COMPANY-{frappe.generate_hash(length=6)}",
                "abbr": "TC",
                "default_currency": "USD",
            })
            company.insert(ignore_permissions=True)
            frappe.db.commit()
            company_name = company.name
            self.test_companies.append(company_name)
        
        # Asegurar que Company tenga el default de 6 meses (o configurarlo explícitamente)
        # El custom field tiene default de 6, así que si no está configurado, será 6
        company_threshold = frappe.db.get_value("Company", company_name, "custom_minimum_expiry_months")
        if company_threshold != 6:
            frappe.db.set_value("Company", company_name, "custom_minimum_expiry_months", 6)
            frappe.db.commit()
        
        # Crear Purchase Receipt sin umbral propio
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company_name)
        self.test_warehouses.append(warehouse.name)
        
        pr = PurchaseReceipt({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": company_name,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
        })
        
        # Validar que usa el valor por defecto (6 meses desde Company o fallback)
        threshold = pr.get_minimum_expiry_months()
        self.assertEqual(threshold, 6, f"Debe usar valor por defecto de 6 meses, pero obtuvo {threshold}. Company tiene {frappe.db.get_value('Company', company_name, 'custom_minimum_expiry_months')}")
    
    def test_get_minimum_expiry_months_from_pr_override(self):
        """
        Test: Purchase Receipt puede tener umbral propio que tiene máxima prioridad
        """
        # Setup: Usar Company existente o crear una básica
        company_name = frappe.db.get_value("Company", {"name": ("!=", "")}, "name")
        if not company_name:
            company = frappe.get_doc({
                "doctype": "Company",
                "company_name": f"TEST-COMPANY-{frappe.generate_hash(length=6)}",
                "abbr": "TC",
                "default_currency": "USD",
            })
            company.insert(ignore_permissions=True)
            frappe.db.commit()
            company_name = company.name
            self.test_companies.append(company_name)
        
        # Configurar umbral en Company existente
        frappe.db.set_value("Company", company_name, "custom_minimum_expiry_months", 6)
        frappe.db.commit()
        
        # Crear Purchase Receipt con umbral propio de 3 meses
        supplier = create_test_supplier(f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}")
        self.test_suppliers.append(supplier.name)
        
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}", company=company_name)
        self.test_warehouses.append(warehouse.name)
        
        pr = PurchaseReceipt({
            "doctype": "Purchase Receipt",
            "supplier": supplier.name,
            "company": company_name,
            "posting_date": today(),
            "set_warehouse": warehouse.name,
            "custom_minimum_expiry_months": 3,
        })
        
        # Validar que usa umbral del Purchase Receipt (máxima prioridad)
        threshold = pr.get_minimum_expiry_months()
        self.assertEqual(threshold, 3, "Debe usar umbral del Purchase Receipt cuando está configurado")

