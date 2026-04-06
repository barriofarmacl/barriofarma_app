# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests E2E para US-001: Registrar Producto de Venta Libre

Historia de Usuario:
Como usuario con rol Inventario
Quiero registrar un Producto Farmacéutico de Venta Libre
Para que el producto esté disponible en el catálogo sin requerir receta

Criterios de Aceptación (Gherkin):
- Dado un usuario con rol Inventario
- Cuando registra un Producto con tipo de dispensación "Venta Libre", principio activo y concentración
- Entonces el sistema guarda el Producto con `has_batch_no = 0` y `has_expiry_date = 1`
- Y `custom_prescription_storage_required = 0`
- Y el Producto aparece en el catálogo con `stock_uom` definido
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cint
from frappe.exceptions import PermissionError

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    get_or_create_item_group,
    get_or_create_uom
)


class TestUS001RegistrarProductoVentaLibre(FrappeTestCase):
    """
    Tests E2E para US-001: Registrar Producto de Venta Libre
    """
    
    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_items = []
        self.test_users = []
    
    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar items de prueba
        for item_name in self.test_items:
            try:
                if frappe.db.exists("Item", item_name):
                    frappe.delete_doc("Item", item_name, force=True, ignore_permissions=True)
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
    
    def _create_inventory_user(self):
        """
        Helper: Crear usuario con rol Inventario para los tests
        """
        username = f"test-inventory-{frappe.generate_hash(length=6)}"
        
        if frappe.db.exists("User", username):
            return frappe.get_doc("User", username)
        
        # Verificar que el rol "Stock Manager" existe (rol estándar de Inventario en ERPNext)
        if not frappe.db.exists("Role", "Stock Manager"):
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": "Stock Manager"
            })
            role.insert(ignore_permissions=True)
            frappe.db.commit()
        
        user = frappe.get_doc({
            "doctype": "User",
            "email": f"{username}@example.com",
            "first_name": "Test",
            "last_name": "Inventory User",
            "username": username,
            "send_welcome_email": 0,
            "user_type": "System User",
            "roles": [{"role": "Stock Manager"}]
        })
        user.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_users.append(user.name)
        return user
    
    def test_us001_dado_usuario_inventario_cuando_registra_producto_venta_libre_entonces_guardado_correcto(self):
        """
        Escenario E2E: Registrar Producto de Venta Libre
        
        Dado un usuario con rol Inventario
        Cuando registra un Producto con tipo de dispensación "Venta Libre", principio activo y concentración
        Entonces el sistema guarda el Producto con `has_batch_no = 0` y `has_expiry_date = 1`
        Y `custom_prescription_storage_required = 0`
        Y el Producto aparece en el catálogo con `stock_uom` definido
        """
        # PREPARACIÓN: Crear usuario con rol Inventario
        inventory_user = self._create_inventory_user()
        frappe.set_user(inventory_user.name)
        
        # PREPARACIÓN: Obtener UOM para stock_uom
        stock_uom = get_or_create_uom("Nos")
        item_group = get_or_create_item_group("Products")
        
        # CUANDO: Registrar Producto de Venta Libre con principio activo y concentración
        item_code = f"TEST-US001-{frappe.generate_hash(length=6)}"
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Paracetamol 500mg - Venta Libre (US-001)",
            "item_group": item_group,
            "stock_uom": stock_uom,
            "is_stock_item": 1,
            "custom_dispensing_type": "Venta Libre",
            "custom_active_principle": "Paracetamol",
            "custom_concentration": "500mg",
            "custom_pharmaceutical_form": "Comprimido",
            # Campos que deben ser ajustados automáticamente por la validación
            "has_batch_no": 0,  # Debe quedar en 0
            "has_expiry_date": 1,  # Debe quedar en 1
            "custom_prescription_storage_required": 0  # Debe quedar en 0
        })
        
        item.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_items.append(item.name)
        
        # ENTONCES: Verificar que el Producto se guardó correctamente
        saved_item = frappe.get_doc("Item", item_code)
        
        # Verificar invariantes de Venta Libre
        self.assertEqual(cint(saved_item.has_batch_no), 0,
                        "Producto de Venta Libre no debe requerir lote (has_batch_no = 0)")
        
        self.assertEqual(cint(saved_item.has_expiry_date), 1,
                        "Producto de Venta Libre debe requerir vencimiento (has_expiry_date = 1)")
        
        self.assertEqual(cint(saved_item.custom_prescription_storage_required), 0,
                        "Producto de Venta Libre no debe requerir almacenamiento de receta")
        
        # Verificar que el Producto aparece en el catálogo con stock_uom definido
        self.assertIsNotNone(saved_item.stock_uom,
                            "El Producto debe tener stock_uom definido")
        self.assertEqual(saved_item.stock_uom, stock_uom,
                        "El stock_uom debe coincidir con el configurado")
        
        # Verificar campos específicos de la historia de usuario
        self.assertEqual(saved_item.custom_dispensing_type, "Venta Libre",
                        "El tipo de dispensación debe ser 'Venta Libre'")
        
        self.assertEqual(saved_item.custom_active_principle, "Paracetamol",
                        "El principio activo debe estar registrado")
        
        self.assertEqual(saved_item.custom_concentration, "500mg",
                        "La concentración debe estar registrada")
    
    def test_us001_validacion_automatica_ajusta_campos_venta_libre(self):
        """
        Escenario: Validación automática ajusta campos para cumplir invariantes
        
        Cuando el usuario intenta crear un producto de Venta Libre con valores incorrectos
        (ej: has_batch_no = 1), la validación debe ajustar automáticamente los campos
        para cumplir con las invariantes de Venta Libre.
        """
        inventory_user = self._create_inventory_user()
        frappe.set_user(inventory_user.name)
        
        stock_uom = get_or_create_uom("Nos")
        item_group = get_or_create_item_group("Products")
        
        item_code = f"TEST-US001-AUTO-{frappe.generate_hash(length=6)}"
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Ibuprofeno 400mg - Venta Libre (Auto)",
            "item_group": item_group,
            "stock_uom": stock_uom,
            "is_stock_item": 1,
            "custom_dispensing_type": "Venta Libre",
            "custom_active_principle": "Ibuprofeno",
            "custom_concentration": "400mg",
            # Valores incorrectos que deben ser ajustados automáticamente
            "has_batch_no": 1,  # Debe ser ajustado a 0
            "has_expiry_date": 0,  # Debe ser ajustado a 1
            "custom_prescription_storage_required": 1  # Debe ser ajustado a 0
        })
        
        item.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_items.append(item.name)
        
        # Verificar que los campos fueron ajustados automáticamente
        saved_item = frappe.get_doc("Item", item_code)
        
        self.assertEqual(cint(saved_item.has_batch_no), 0,
                        "has_batch_no debe ser ajustado automáticamente a 0")
        
        self.assertEqual(cint(saved_item.has_expiry_date), 1,
                        "has_expiry_date debe ser ajustado automáticamente a 1")
        
        self.assertEqual(cint(saved_item.custom_prescription_storage_required), 0,
                        "custom_prescription_storage_required debe ser ajustado automáticamente a 0")
    
    def test_us001_producto_aparece_en_catalogo(self):
        """
        Escenario: Producto aparece en el catálogo después de ser registrado
        
        Verificar que un producto de Venta Libre registrado puede ser consultado
        en el catálogo y está disponible para uso en el sistema.
        """
        inventory_user = self._create_inventory_user()
        frappe.set_user(inventory_user.name)
        
        stock_uom = get_or_create_uom("Nos")
        item_group = get_or_create_item_group("Products")
        
        item_code = f"TEST-US001-CAT-{frappe.generate_hash(length=6)}"
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Acetaminofén 500mg - Venta Libre (Catálogo)",
            "item_group": item_group,
            "stock_uom": stock_uom,
            "is_stock_item": 1,
            "custom_dispensing_type": "Venta Libre",
            "custom_active_principle": "Acetaminofén",
            "custom_concentration": "500mg"
        })
        
        item.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_items.append(item.name)
        
        # Verificar que el producto puede ser consultado en el catálogo
        # (usando frappe.get_doc y frappe.db.exists)
        self.assertTrue(frappe.db.exists("Item", item_code),
                       "El producto debe existir en la base de datos")
        
        catalog_item = frappe.get_doc("Item", item_code)
        self.assertIsNotNone(catalog_item,
                            "El producto debe poder ser consultado desde el catálogo")
        
        self.assertEqual(catalog_item.item_code, item_code,
                        "El código del producto debe coincidir")
        
        # Verificar que tiene stock_uom definido (requisito del catálogo)
        self.assertIsNotNone(catalog_item.stock_uom,
                            "El producto en el catálogo debe tener stock_uom definido")
        
        # Verificar que está marcado como stock_item
        self.assertEqual(cint(catalog_item.is_stock_item), 1,
                        "El producto debe estar marcado como stock_item para aparecer en inventario")

