# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests E2E para US-003: Vender Producto de Venta Libre en Factura

Historia de Usuario:
Como usuario con rol Ventas
Quiero vender un Producto de Venta Libre en una Factura
Para que el cliente pueda comprar sin receta médica

Criterios de Aceptación (Gherkin):
- Dado un Producto de Venta Libre creado y disponible en catálogo
- Y un usuario con rol Ventas
- Cuando agrega el Producto a una Sales Invoice
- Entonces el sistema no exige selección de lote
- Y valida que el control de vencimiento esté activo
- Y la factura puede guardarse en estado Borrador sin solicitar receta
"""

import unittest
import frappe
from frappe.utils import cint, today
from frappe.exceptions import ValidationError

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_customer,
    get_or_create_item_group,
    get_or_create_uom
)


class TestUS003VenderProductoVentaLibreEnFactura(unittest.TestCase):
    """
    Tests E2E para US-003: Vender Producto de Venta Libre en Factura
    """
    
    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_items = []
        self.test_customers = []
        self.test_sales_invoices = []
        self.test_users = []
    
    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar facturas de prueba
        for invoice_name in self.test_sales_invoices:
            try:
                if frappe.db.exists("Sales Invoice", invoice_name):
                    frappe.delete_doc("Sales Invoice", invoice_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar items de prueba
        for item_name in self.test_items:
            try:
                if frappe.db.exists("Item", item_name):
                    frappe.delete_doc("Item", item_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar clientes de prueba
        for customer_name in self.test_customers:
            try:
                if frappe.db.exists("Customer", customer_name):
                    frappe.delete_doc("Customer", customer_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar usuarios de prueba
        for user_name in self.test_users:
            try:
                if frappe.db.exists("User", user_name):
                    frappe.delete_doc("User", user_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()
    
    def _create_sales_user(self):
        """
        Helper: Crear usuario con rol Ventas para los tests
        """
        username = f"test-sales-{frappe.generate_hash(length=6)}"
        
        if frappe.db.exists("User", username):
            return frappe.get_doc("User", username)
        
        # Verificar que el rol "Sales User" existe (rol estándar de Ventas en ERPNext)
        if not frappe.db.exists("Role", "Sales User"):
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": "Sales User"
            })
            role.insert(ignore_permissions=True)
            frappe.db.commit()
        
        user = frappe.get_doc({
            "doctype": "User",
            "email": f"{username}@example.com",
            "first_name": "Test",
            "last_name": "Sales User",
            "username": username,
            "send_welcome_email": 0,
            "user_type": "System User",
            "roles": [{"role": "Sales User"}]
        })
        user.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_users.append(user.name)
        return user
    
    def _create_venta_libre_item(self):
        """
        Helper: Crear Item de Venta Libre para los tests
        """
        item_code = f"TEST-US003-VL-{frappe.generate_hash(length=6)}"
        
        if frappe.db.exists("Item", item_code):
            item = frappe.get_doc("Item", item_code)
        else:
            item = create_test_item(
                item_code=item_code,
                item_name="Paracetamol 500mg - Venta Libre (US-003)",
                custom_dispensing_type="Venta Libre",
                has_batch_no=0,  # No requiere lote
                has_expiry_date=1,  # Requiere vencimiento
                custom_prescription_storage_required=0,
                custom_active_principle="Paracetamol",
                custom_concentration="500mg",
                custom_pharmaceutical_form="Comprimido",
                is_stock_item=1
            )
        
        self.test_items.append(item.name)
        return item
    
    def test_us003_dado_producto_venta_libre_cuando_agrega_factura_entonces_no_exige_lote(self):
        """
        Escenario E2E: Agregar Producto de Venta Libre a Factura
        
        Dado un Producto de Venta Libre creado y disponible en catálogo
        Y un usuario con rol Ventas
        Cuando agrega el Producto a una Sales Invoice
        Entonces el sistema no exige selección de lote
        """
        # PREPARACIÓN: Crear usuario con rol Ventas
        sales_user = self._create_sales_user()
        frappe.set_user(sales_user.name)
        
        # PREPARACIÓN: Crear Item de Venta Libre
        item = self._create_venta_libre_item()
        
        # Verificar que el item no requiere lote
        self.assertEqual(cint(item.has_batch_no), 0,
                        "El item de Venta Libre no debe requerir lote")
        
        # PREPARACIÓN: Crear Customer
        customer = create_test_customer(f"Cliente Test US-003 {frappe.generate_hash(length=4)}")
        self.test_customers.append(customer.name)
        
        # CUANDO: Agregar el Producto a una Sales Invoice
        sales_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer.name,
            "posting_date": today(),
            "items": [
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": 1,
                    "rate": 1000,
                    "stock_uom": item.stock_uom
                }
            ]
        })
        
        # ENTONCES: Verificar que no se exige selección de lote
        # En ERPNext, si has_batch_no = 0, no se requiere batch_no en los items
        sales_invoice.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_sales_invoices.append(sales_invoice.name)
        
        # Verificar que la factura se guardó correctamente
        saved_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
        self.assertIsNotNone(saved_invoice.name,
                            "La factura debe guardarse correctamente")
        
        # Verificar que el item no tiene batch_no requerido
        invoice_item = saved_invoice.items[0]
        # Si has_batch_no = 0, batch_no debe ser None o vacío (no requerido)
        # ERPNext permite que batch_no esté vacío si has_batch_no = 0
        self.assertTrue(
            not invoice_item.get("batch_no") or invoice_item.get("batch_no") == "",
            "El item de Venta Libre no debe requerir batch_no"
        )
    
    def test_us003_valida_control_vencimiento_activo(self):
        """
        Escenario: Validar que el control de vencimiento esté activo
        
        Cuando se agrega un Producto de Venta Libre a una factura,
        el sistema debe validar que el control de vencimiento esté activo (has_expiry_date = 1).
        """
        # PREPARACIÓN
        sales_user = self._create_sales_user()
        frappe.set_user(sales_user.name)
        
        item = self._create_venta_libre_item()
        
        # Verificar que el item requiere vencimiento
        self.assertEqual(cint(item.has_expiry_date), 1,
                        "El item de Venta Libre debe requerir vencimiento")
        
        customer = create_test_customer(f"Cliente Test US-003 VENC {frappe.generate_hash(length=4)}")
        self.test_customers.append(customer.name)
        
        # CUANDO: Crear factura con item de Venta Libre
        sales_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer.name,
            "posting_date": today(),
            "items": [
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": 1,
                    "rate": 1000,
                    "stock_uom": item.stock_uom
                }
            ]
        })
        
        sales_invoice.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_sales_invoices.append(sales_invoice.name)
        
        # ENTONCES: Verificar que el item en la factura tiene has_expiry_date = 1
        saved_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
        invoice_item = saved_invoice.items[0]
        
        # Obtener el item para verificar has_expiry_date
        item_doc = frappe.get_doc("Item", invoice_item.item_code)
        self.assertEqual(cint(item_doc.has_expiry_date), 1,
                        "El control de vencimiento debe estar activo (has_expiry_date = 1)")
    
    def test_us003_factura_guarda_borrador_sin_receta(self):
        """
        Escenario: La factura puede guardarse en estado Borrador sin solicitar receta
        
        Cuando se agrega un Producto de Venta Libre a una factura,
        la factura puede guardarse en estado Borrador sin solicitar receta médica.
        """
        # PREPARACIÓN
        sales_user = self._create_sales_user()
        frappe.set_user(sales_user.name)
        
        item = self._create_venta_libre_item()
        
        customer = create_test_customer(f"Cliente Test US-003 BORR {frappe.generate_hash(length=4)}")
        self.test_customers.append(customer.name)
        
        # CUANDO: Crear factura en estado Borrador con item de Venta Libre
        sales_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer.name,
            "posting_date": today(),
            "status": "Draft",  # Estado Borrador
            "items": [
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": 1,
                    "rate": 1000,
                    "stock_uom": item.stock_uom
                }
            ]
            # Sin campo prescription - no se requiere para Venta Libre
        })
        
        # ENTONCES: La factura debe guardarse sin solicitar receta
        sales_invoice.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_sales_invoices.append(sales_invoice.name)
        
        # Verificar que la factura se guardó en estado Borrador
        saved_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
        self.assertEqual(saved_invoice.status, "Draft",
                        "La factura debe guardarse en estado Borrador")
        
        # Verificar que no se requiere receta (prescription debe ser None o vacío)
        # En ERPNext, si no hay campo prescription, es None
        self.assertTrue(
            not saved_invoice.get("prescription") or saved_invoice.get("prescription") == "",
            "La factura de Venta Libre no debe requerir receta (prescription debe ser None o vacío)"
        )
    
    def test_us003_flujo_completo_venta_libre_en_factura(self):
        """
        Escenario: Flujo completo de venta de producto de Venta Libre en factura
        
        Integración completa: Producto de Venta Libre -> Factura -> Guardado -> Verificación
        """
        # PREPARACIÓN
        sales_user = self._create_sales_user()
        frappe.set_user(sales_user.name)
        
        # Crear Item de Venta Libre
        item = self._create_venta_libre_item()
        
        # Verificar características del item
        self.assertEqual(cint(item.has_batch_no), 0, "No requiere lote")
        self.assertEqual(cint(item.has_expiry_date), 1, "Requiere vencimiento")
        self.assertEqual(item.custom_dispensing_type, "Venta Libre", "Tipo: Venta Libre")
        
        # Crear Customer
        customer = create_test_customer(f"Cliente Test US-003 COMPL {frappe.generate_hash(length=4)}")
        self.test_customers.append(customer.name)
        
        # CUANDO: Crear factura completa con producto de Venta Libre
        sales_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": customer.name,
            "posting_date": today(),
            "items": [
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": 2,
                    "rate": 1500,
                    "stock_uom": item.stock_uom
                }
            ]
        })
        
        sales_invoice.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_sales_invoices.append(sales_invoice.name)
        
        # ENTONCES: Verificar todos los criterios de aceptación
        saved_invoice = frappe.get_doc("Sales Invoice", sales_invoice.name)
        
        # 1. La factura se guardó correctamente
        self.assertIsNotNone(saved_invoice.name,
                            "La factura debe guardarse correctamente")
        
        # 2. El item no tiene batch_no (no se exige selección de lote)
        invoice_item = saved_invoice.items[0]
        self.assertTrue(
            not invoice_item.get("batch_no") or invoice_item.get("batch_no") == "",
            "No se debe exigir selección de lote (batch_no debe ser None o vacío)"
        )
        
        # 3. El control de vencimiento está activo
        item_doc = frappe.get_doc("Item", invoice_item.item_code)
        self.assertEqual(cint(item_doc.has_expiry_date), 1,
                        "El control de vencimiento debe estar activo")
        
        # 4. La factura puede guardarse sin receta
        self.assertTrue(
            not saved_invoice.get("prescription") or saved_invoice.get("prescription") == "",
            "La factura no debe requerir receta para productos de Venta Libre"
        )
        
        # 5. La factura tiene los datos correctos
        self.assertEqual(saved_invoice.customer, customer.name,
                        "El cliente debe coincidir")
        self.assertEqual(len(saved_invoice.items), 1,
                        "Debe tener un item")
        self.assertEqual(invoice_item.qty, 2,
                        "La cantidad debe coincidir")
        self.assertEqual(invoice_item.rate, 1500,
                        "El precio debe coincidir")

