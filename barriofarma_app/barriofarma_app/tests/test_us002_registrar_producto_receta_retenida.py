# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests E2E para US-002: Registrar Producto de Receta Retenida

Historia de Usuario:
Como usuario con rol Inventario
Quiero registrar un Producto Farmacéutico de Receta Retenida
Para que el producto esté disponible en el catálogo requiriendo receta médica

Criterios de Aceptación (Gherkin):
- Dado un usuario con rol Inventario
- Cuando registra un Producto con tipo de dispensación "Venta con Receta Retenida" y un registro sanitario válido
- Entonces el sistema guarda el Producto con `has_batch_no = 1`, `has_expiry_date = 1` y `custom_prescription_storage_required = 1`
- Y si falta `custom_sanitary_registration`, el sistema rechaza el guardado con un error de validación
"""

import unittest
import frappe
from frappe.utils import cint
from frappe.exceptions import ValidationError

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    get_or_create_item_group,
    get_or_create_uom
)


class TestUS002RegistrarProductoRecetaRetenida(unittest.TestCase):
    """
    Tests E2E para US-002: Registrar Producto de Receta Retenida
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
    
    def test_us002_dado_usuario_inventario_cuando_registra_producto_receta_retenida_entonces_guardado_correcto(self):
        """
        Escenario E2E: Registrar Producto de Receta Retenida con registro sanitario válido
        
        Dado un usuario con rol Inventario
        Cuando registra un Producto con tipo de dispensación "Venta con Receta Retenida" y un registro sanitario válido
        Entonces el sistema guarda el Producto con `has_batch_no = 1`, `has_expiry_date = 1` y `custom_prescription_storage_required = 1`
        """
        # PREPARACIÓN: Crear usuario con rol Inventario
        inventory_user = self._create_inventory_user()
        frappe.set_user(inventory_user.name)
        
        # PREPARACIÓN: Obtener UOM y Item Group
        stock_uom = get_or_create_uom("Nos")
        item_group = get_or_create_item_group("Products")
        
        # CUANDO: Registrar Producto de Receta Retenida con registro sanitario válido
        item_code = f"TEST-US002-{frappe.generate_hash(length=6)}"
        sanitary_registration = "F-12345/24"
        
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Clonazepam 2mg - Receta Retenida (US-002)",
            "item_group": item_group,
            "stock_uom": stock_uom,
            "is_stock_item": 1,
            "custom_dispensing_type": "Venta con Receta Retenida",
            "custom_sanitary_registration": sanitary_registration,
            "custom_active_principle": "Clonazepam",
            "custom_concentration": "2mg",
            "custom_pharmaceutical_form": "Comprimido",
            # Campos que deben ser ajustados automáticamente o requeridos
            "has_batch_no": 1,  # Requerido para Receta Retenida
            "has_expiry_date": 1,  # Requerido para Receta Retenida
            "custom_prescription_storage_required": 1  # Debe quedar en 1
        })
        
        item.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_items.append(item.name)
        
        # ENTONCES: Verificar que el Producto se guardó correctamente
        saved_item = frappe.get_doc("Item", item_code)
        
        # Verificar invariantes de Receta Retenida
        self.assertEqual(cint(saved_item.has_batch_no), 1,
                        "Producto de Receta Retenida debe requerir lote (has_batch_no = 1)")
        
        self.assertEqual(cint(saved_item.has_expiry_date), 1,
                        "Producto de Receta Retenida debe requerir vencimiento (has_expiry_date = 1)")
        
        self.assertEqual(cint(saved_item.custom_prescription_storage_required), 1,
                        "Producto de Receta Retenida debe requerir almacenamiento de receta")
        
        # Verificar campos específicos de la historia de usuario
        self.assertEqual(saved_item.custom_dispensing_type, "Venta con Receta Retenida",
                        "El tipo de dispensación debe ser 'Venta con Receta Retenida'")
        
        self.assertEqual(saved_item.custom_sanitary_registration, sanitary_registration,
                        "El registro sanitario debe estar registrado")
        
        self.assertEqual(saved_item.custom_active_principle, "Clonazepam",
                        "El principio activo debe estar registrado")
        
        self.assertEqual(saved_item.custom_concentration, "2mg",
                        "La concentración debe estar registrada")
        
        # Verificar que el Producto aparece en el catálogo con stock_uom definido
        self.assertIsNotNone(saved_item.stock_uom,
                            "El Producto debe tener stock_uom definido")
        self.assertEqual(saved_item.stock_uom, stock_uom,
                        "El stock_uom debe coincidir con el configurado")
    
    def test_us002_validacion_rechaza_sin_registro_sanitario(self):
        """
        Escenario: Validación rechaza guardado cuando falta registro sanitario
        
        Cuando el usuario intenta crear un producto de Receta Retenida sin registro sanitario,
        el sistema debe rechazar el guardado con un error de validación.
        """
        inventory_user = self._create_inventory_user()
        frappe.set_user(inventory_user.name)
        
        stock_uom = get_or_create_uom("Nos")
        item_group = get_or_create_item_group("Products")
        
        item_code = f"TEST-US002-SIN-REG-{frappe.generate_hash(length=6)}"
        
        # Intentar crear sin registro sanitario debe fallar
        with self.assertRaises(ValidationError) as context:
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_name": "Diazepam 10mg - Sin Registro (US-002)",
                "item_group": item_group,
                "stock_uom": stock_uom,
                "is_stock_item": 1,
                "custom_dispensing_type": "Venta con Receta Retenida",
                # Sin custom_sanitary_registration - debe fallar
                "custom_active_principle": "Diazepam",
                "custom_concentration": "10mg",
                "has_batch_no": 1,
                "has_expiry_date": 1,
                "custom_prescription_storage_required": 1
            })
            
            item.insert(ignore_permissions=True)
            frappe.db.commit()
            self.test_items.append(item.name)
        
        # Verificar que el error menciona registro sanitario
        error_message = str(context.exception).lower()
        self.assertTrue(
            "registro sanitario" in error_message or
            "sanitary_registration" in error_message or
            "campo obligatorio" in error_message,
            f"El error debe mencionar registro sanitario: {error_message}"
        )
        
        # Verificar que el item NO fue creado
        self.assertFalse(
            frappe.db.exists("Item", item_code),
            "El item no debe existir si faltó el registro sanitario"
        )
    
    def test_us002_validacion_automatica_ajusta_campos_receta_retenida(self):
        """
        Escenario: Validación automática ajusta campos para cumplir invariantes
        
        Cuando el usuario intenta crear un producto de Receta Retenida con valores incorrectos
        (ej: has_batch_no = 0), la validación debe rechazar o ajustar automáticamente
        según corresponda.
        """
        inventory_user = self._create_inventory_user()
        frappe.set_user(inventory_user.name)
        
        stock_uom = get_or_create_uom("Nos")
        item_group = get_or_create_item_group("Products")
        
        item_code = f"TEST-US002-AUTO-{frappe.generate_hash(length=6)}"
        
        # Intentar crear con has_batch_no = 0 debe fallar (requerido para Receta Retenida)
        with self.assertRaises(ValidationError) as context:
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_name": "Lorazepam 1mg - Receta Retenida (Auto)",
                "item_group": item_group,
                "stock_uom": stock_uom,
                "is_stock_item": 1,
                "custom_dispensing_type": "Venta con Receta Retenida",
                "custom_sanitary_registration": "F-67890/24",
                "custom_active_principle": "Lorazepam",
                "custom_concentration": "1mg",
                # Valores incorrectos que deben causar error
                "has_batch_no": 0,  # Debe ser 1 para Receta Retenida - debe fallar
                "has_expiry_date": 1,
                "custom_prescription_storage_required": 1
            })
            
            item.insert(ignore_permissions=True)
            frappe.db.commit()
            self.test_items.append(item.name)
        
        # Verificar que el error menciona lote o batch
        error_message = str(context.exception).lower()
        self.assertTrue(
            "lote" in error_message or
            "batch" in error_message or
            "invariante" in error_message,
            f"El error debe mencionar lote/batch: {error_message}"
        )
    
    def test_us002_producto_aparece_en_catalogo(self):
        """
        Escenario: Producto aparece en el catálogo después de ser registrado
        
        Verificar que un producto de Receta Retenida registrado puede ser consultado
        en el catálogo y está disponible para uso en el sistema.
        """
        inventory_user = self._create_inventory_user()
        frappe.set_user(inventory_user.name)
        
        stock_uom = get_or_create_uom("Nos")
        item_group = get_or_create_item_group("Products")
        
        item_code = f"TEST-US002-CAT-{frappe.generate_hash(length=6)}"
        
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Alprazolam 0.5mg - Receta Retenida (Catálogo)",
            "item_group": item_group,
            "stock_uom": stock_uom,
            "is_stock_item": 1,
            "custom_dispensing_type": "Venta con Receta Retenida",
            "custom_sanitary_registration": "F-99999/24",
            "custom_active_principle": "Alprazolam",
            "custom_concentration": "0.5mg",
            "has_batch_no": 1,
            "has_expiry_date": 1,
            "custom_prescription_storage_required": 1
        })
        
        item.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_items.append(item.name)
        
        # Verificar que el producto puede ser consultado en el catálogo
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
        
        # Verificar que tiene registro sanitario (requisito específico de Receta Retenida)
        self.assertIsNotNone(catalog_item.custom_sanitary_registration,
                            "El producto de Receta Retenida debe tener registro sanitario")

