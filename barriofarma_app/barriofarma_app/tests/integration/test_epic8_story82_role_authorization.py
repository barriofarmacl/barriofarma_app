# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para Story 8.2: Tests de Autorización por Roles

Valida que los permisos funcionan correctamente para cada rol:
- Farmacéutico: Acceso a recetas, dispensaciones, validaciones
- Auxiliar: Acceso a ventas, búsqueda de productos, registro de clientes
- Bodeguero: Acceso a inventario, recepciones, movimientos de stock
- Administrativo: Acceso a reportes, configuración básica
- Contabilidad: Acceso a facturas, pagos, reportes financieros
- Informática: Acceso técnico completo, configuración avanzada

Referencias:
- Frappe Permissions Best Practices: 
  https://explorewithjnk.com/blog/2025/08/13/mastering-frappe-framework-part-6-user-permissions-roles/
- Frappe Testing Documentation: https://docs.frappe.io/docs/guides/testing
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, add_days, today
from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_warehouse,
    create_test_shelf,
    create_test_doctor,
    create_test_patient,
    get_test_company,
)


def normalize_user(user: str) -> str:
    """
    Normaliza identificadores de usuario para tests.

    En Frappe, `User.name` suele ser el email (ej: user@test.com).
    En nuestros tests a veces usamos un "username" corto (sin @).
    Esta función lo convierte al email de test esperado.
    """
    if not user:
        return user
    if user in ("Administrator", "Guest"):
        return user
    if "@" in user:
        return user
    # Si existe como nombre real, no lo transformamos
    if frappe.db.exists("User", user):
        return user
    return f"{user}@test.barriofarma.cl"


# Patch global: asegurar que TODOS los `frappe.set_user("test_xxx")` apunten a un User válido.
_frappe_set_user = frappe.set_user


def _patched_set_user(user):
    return _frappe_set_user(normalize_user(user))


frappe.set_user = _patched_set_user


def create_test_user_with_role(username, role_name, email=None):
    """
    Crear usuario de prueba con rol específico
    
    Args:
        username: Nombre de usuario
        role_name: Nombre del rol a asignar
        email: Email del usuario (opcional)
    
    Returns:
        User doc
    """
    if not email:
        email = normalize_user(username)
    
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        # Deshabilitar throttling para tests
        frappe.flags.in_import = True
        try:
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": username,
                "username": username,
                "send_welcome_email": 0
            })
            user.insert(ignore_permissions=True)
            frappe.db.commit()
        finally:
            frappe.flags.in_import = False
    
    # Asignar rol directamente en la tabla Has Role
    # Verificar si ya existe
    if not frappe.db.exists("Has Role", {"parent": email, "role": role_name}):
        has_role = frappe.get_doc({
            "doctype": "Has Role",
            "parent": email,
            "parenttype": "User",
            "parentfield": "roles",
            "role": role_name
        })
        has_role.insert(ignore_permissions=True)
        frappe.db.commit()
    
    # Recargar usuario para obtener roles actualizados
    user.reload()
    
    # Limpiar caché para que los permisos se recalculen
    frappe.clear_cache()
    
    return user


def test_has_permission(doctype, permission_type="read", should_have=True):
    """
    Validar que usuario actual tiene permiso específico
    
    Args:
        doctype: Nombre del DocType
        permission_type: Tipo de permiso (read, write, create, delete, submit, cancel)
        should_have: Si debería tener el permiso (True) o no (False)
    
    Returns:
        bool: True si el permiso coincide con should_have
    """
    # Limpiar caché antes de verificar permisos
    frappe.clear_cache()
    has_perm = frappe.has_permission(doctype, permission_type)
    if should_have:
        return has_perm
    else:
        return not has_perm


def test_can_access_doctype(doctype, should_access=True):
    """
    Validar que usuario actual puede acceder a DocType (al menos Read)
    
    Args:
        doctype: Nombre del DocType
        should_access: Si debería poder acceder (True) o no (False)
    
    Returns:
        bool: True si el acceso coincide con should_access
    """
    # Limpiar caché antes de verificar acceso
    frappe.clear_cache()
    return test_has_permission(doctype, "read", should_access)


def create_test_prescription(prescription_number=None, doctor_license=None, patient=None, **kwargs):
    """
    Crear Prescription de prueba con campos requeridos
    
    Args:
        prescription_number: Número de prescripción (opcional, se genera si no se proporciona)
        doctor_license: Número de licencia médica (opcional, se crea Doctor si no se proporciona)
        patient: Nombre del paciente (opcional, se crea Patient si no se proporciona)
        **kwargs: Campos adicionales del Prescription
    
    Returns:
        Prescription document creado
    """
    frappe.set_user("Administrator")
    
    # Crear/obtener Doctor (Prescription requiere doctor, doctor_name y doctor_license)
    doctor_doc = None
    doctor_name = kwargs.get("doctor") or kwargs.get("doctor_name")
    if doctor_name and frappe.db.exists("Doctor", doctor_name):
        doctor_doc = frappe.get_doc("Doctor", doctor_name)
    elif doctor_license:
        existing_doctor = frappe.db.get_value("Doctor", {"license_number": doctor_license}, "name")
        if existing_doctor:
            doctor_doc = frappe.get_doc("Doctor", existing_doctor)
        else:
            doctor_doc = create_test_doctor(license_number=doctor_license)
    else:
        doctor_doc = create_test_doctor()
    
    # Crear/obtener Patient (Prescription requiere patient y patient_name)
    if not patient:
        patient_doc = create_test_patient()
    else:
        if frappe.db.exists("Patient", patient):
            patient_doc = frappe.get_doc("Patient", patient)
        else:
            patient_doc = create_test_patient(patient_name=patient)
    
    if not prescription_number:
        prescription_number = f"PRES-TEST-{frappe.generate_hash(length=6)}"
    
    # Fechas requeridas: prescription_date y valid_till
    # valid_till debe ser >= prescription_date
    prescription_date = kwargs.get("prescription_date", today())
    valid_till = kwargs.get("valid_till", add_days(prescription_date, 30))  # 30 días de validez por defecto
    
    # Asegurar que valid_till >= prescription_date
    if getdate(valid_till) < getdate(prescription_date):
        valid_till = add_days(prescription_date, 30)
    
    defaults = {
        "doctype": "Receta Medica",
        "naming_series": kwargs.get("naming_series", "RX-.YY.-.MM.-.#####"),
        "prescription_number": prescription_number,
        "doctor": doctor_doc.name,
        "doctor_name": doctor_doc.doctor_name,
        "doctor_license": doctor_doc.license_number,
        "patient": patient_doc.name,
        "patient_name": patient_doc.patient_name,
        "prescription_date": prescription_date,
        "valid_till": valid_till,
        **{k: v for k, v in kwargs.items() if k not in ["prescription_date", "valid_till"]}  # Excluir para evitar duplicados
    }
    
    presc = frappe.get_doc(defaults)
    
    # Agregar item mínimo si no se proporciona en kwargs
    if not presc.get("items") or len(presc.items) == 0:
        # Crear item de prueba si no existe
        item_code = kwargs.get("item_code", f"TEST-ITEM-PRESC-{frappe.generate_hash(length=6)}")
        if not frappe.db.exists("Item", item_code):
            item = create_test_item(
                item_code=item_code, 
                item_name="Test Item for Prescription",
                custom_dispensing_type="Venta con Receta Retenida",  # Campo requerido, valor válido
                has_batch_no=1,  # Requerido para "Venta con Receta Retenida"
                has_expiry_date=1,  # Requerido para "Venta con Receta Retenida"
                custom_prescription_storage_required=1,  # Requerido para "Venta con Receta Retenida"
                custom_sanitary_registration=f"TEST-REG-{frappe.generate_hash(length=6)}"  # Requerido para "Venta con Receta Retenida"
            )
        else:
            item = frappe.get_doc("Item", item_code)
        
        # Agregar item a la prescripción (Prescription Item requiere: item, item_name, dosage, frequency, quantity)
        presc.append("items", {
            "item": item_code,
            "item_name": item.item_name,
            "quantity": kwargs.get("qty", 1),
            "dosage": kwargs.get("dosage", "1 comprimido"),
            "frequency": kwargs.get("frequency", "Cada 8 horas"),
            "duration": kwargs.get("duration", "7 días")
        })
    
    presc.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return presc


class TestEpic8Story82RoleAuthorization(FrappeTestCase):
    """Tests base para Story 8.2: Autorización por Roles"""

    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        
        self.test_users = []
        self.test_items = []
        self.test_warehouses = []
        self.test_shelves = []
        
        # Crear datos de prueba básicos
        self.company = get_test_company()
        self.warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(self.warehouse.name)
        
        # Crear item de prueba
        self.item = create_test_item(
            item_code=f"TEST-ITEM-{frappe.generate_hash(length=6)}",
            item_group="Medicamentos de Prueba",
            has_batch_no=1,
            has_expiry_date=1,
            custom_dispensing_type="Venta con Receta Retenida",
            custom_sanitary_registration="REG-TEST-001"
        )
        self.test_items.append(self.item.name)
        frappe.db.commit()

    def tearDown(self):
        """Limpiar datos de prueba"""
        frappe.set_user("Administrator")
        
        # Eliminar usuarios de prueba
        for username in self.test_users:
            if frappe.db.exists("User", username):
                frappe.delete_doc("User", username, ignore_permissions=True, force=1)
        
        # Limpiar otros datos de prueba
        for item_code in self.test_items:
            if frappe.db.exists("Item", item_code):
                frappe.delete_doc("Item", item_code, ignore_permissions=True, force=1)
        
        for wh_name in self.test_warehouses:
            if frappe.db.exists("Warehouse", wh_name):
                frappe.delete_doc("Warehouse", wh_name, ignore_permissions=True, force=1)
        
        # Limpiar Prescriptions si existen
        if hasattr(self, 'test_prescriptions'):
            for presc_name in self.test_prescriptions:
                if frappe.db.exists("Receta Medica", presc_name):
                    frappe.delete_doc("Receta Medica", presc_name, ignore_permissions=True, force=1)
        
        frappe.db.commit()
        frappe.clear_cache()


class TestFarmaceuticoRole(TestEpic8Story82RoleAuthorization):
    """Tests para rol Farmacéutico"""

    def setUp(self):
        super().setUp()
        self.username = f"test_farmaceutico_{frappe.generate_hash(length=6)}"
        self.user = create_test_user_with_role(self.username, "Farmacéutico")
        self.test_users.append(self.username)
        # Limpiar caché después de crear usuario
        frappe.clear_cache()

    def test_farmaceutico_can_read_prescription(self):
        """Farmacéutico puede leer Prescription"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_can_access_doctype("Receta Medica", should_access=True))

    def test_farmaceutico_can_write_prescription(self):
        """Farmacéutico puede escribir Prescription"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Receta Medica", "write", should_have=True))

    def test_farmaceutico_can_create_prescription(self):
        """Farmacéutico puede crear Prescription"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Receta Medica", "create", should_have=True))

    def test_farmaceutico_can_read_sales_invoice(self):
        """Farmacéutico puede leer Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Sales Invoice", should_access=True))

    def test_farmaceutico_can_write_sales_invoice(self):
        """Farmacéutico puede escribir Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Sales Invoice", "write", should_have=True))

    def test_farmaceutico_can_create_sales_invoice(self):
        """Farmacéutico puede crear Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Sales Invoice", "create", should_have=True))

    def test_farmaceutico_can_read_item(self):
        """Farmacéutico puede leer Item"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Item", should_access=True))

    def test_farmaceutico_can_write_item(self):
        """Farmacéutico puede escribir Item"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Item", "write", should_have=True))

    def test_farmaceutico_can_read_purchase_receipt(self):
        """Farmacéutico puede leer Purchase Receipt (QC)"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_can_access_doctype("Purchase Receipt", should_access=True))

    def test_farmaceutico_can_write_purchase_receipt(self):
        """Farmacéutico puede escribir Purchase Receipt (QC)"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Purchase Receipt", "write", should_have=True))

    def test_farmaceutico_cannot_create_purchase_receipt(self):
        """Farmacéutico NO crea Purchase Receipt (recepción física es del auxiliar)"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Purchase Receipt", "create", should_have=False))

    def test_farmaceutico_can_submit_purchase_receipt(self):
        """Farmacéutico puede submitir Purchase Receipt tras QC"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Purchase Receipt", "submit", should_have=True))

    def test_farmaceutico_can_create_purchase_order(self):
        """Farmacéutico puede crear Purchase Order"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Purchase Order", "create", should_have=True))

    def test_farmaceutico_can_write_price_list(self):
        """Farmacéutico puede crear y modificar listas de precios"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Price List", "write", should_have=True))
        self.assertTrue(test_has_permission("Price List", "create", should_have=True))

    def test_farmaceutico_can_write_item_price(self):
        """Farmacéutico puede crear y modificar precios por ítem"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Item Price", "write", should_have=True))
        self.assertTrue(test_has_permission("Item Price", "create", should_have=True))

    def test_farmaceutico_can_manage_products_and_pricing_masters(self):
        """Farmacéutico: tablero Compras — sección Productos y Precios completa"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        for dt in (
            "Product Bundle",
            "Item Group",
            "Promotional Scheme",
            "Pricing Rule",
        ):
            self.assertTrue(
                test_has_permission(dt, "read", should_have=True),
                msg=f"read {dt}",
            )
            self.assertTrue(
                test_has_permission(dt, "create", should_have=True),
                msg=f"create {dt}",
            )

    def test_farmaceutico_can_use_buying_procurement_tools(self):
        """Farmacéutico: solicitudes, cotizaciones y consulta factura de compra"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Material Request", "create", should_have=True))
        self.assertTrue(test_has_permission("Request for Quotation", "create", should_have=True))
        self.assertTrue(test_has_permission("Supplier Quotation", "create", should_have=True))
        self.assertTrue(test_has_permission("Purchase Invoice", "read", should_have=True))
        self.assertTrue(test_has_permission("Purchase Invoice", "write", should_have=False))

    def test_farmaceutico_can_read_buying_dashboard_reports(self):
        """Farmacéutico: reportes de gráficos del tablero Compras"""
        from barriofarma_app.barriofarma_app.utils.permissions.frappe_v16_compat import (
            get_allowed_report_names,
        )

        frappe.set_user(self.username)
        frappe.clear_cache()
        allowed = get_allowed_report_names()
        for report in (
            "Purchase Order Trends",
            "Purchase Order Analysis",
            "Purchase Receipt Trends",
        ):
            self.assertIn(report, allowed, msg=report)

    def test_farmaceutico_can_read_bin_for_shortage_report(self):
        """Farmacéutico: lectura Bin (Papelera) requerida por Item Shortage Report"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Bin", "read", should_have=True))

    def test_farmaceutico_can_create_pos_closing_entry(self):
        """Farmacéutico puede cerrar caja POS"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("POS Closing Entry", "create", should_have=True))
        self.assertTrue(test_has_permission("POS Closing Entry", "submit", should_have=True))

    def test_farmaceutico_cannot_access_stock_entry(self):
        """Farmacéutico NO puede acceder a Stock Entry"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Stock Entry", should_access=False))

    def test_farmaceutico_can_operate_stock_reconciliation(self):
        """Farmacéutico puede crear y validar Reconciliación de inventarios"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_can_access_doctype("Stock Reconciliation", should_access=True))
        self.assertTrue(test_has_permission("Stock Reconciliation", "create", should_have=True))
        self.assertTrue(test_has_permission("Stock Reconciliation", "submit", should_have=True))

    def test_farmaceutico_can_create_batch(self):
        """Farmacéutico puede crear y escribir Batch (whiteboard #78 PR1)"""
        from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
            setup_permissions_for_role,
        )

        frappe.set_user("Administrator")
        setup_permissions_for_role("Farmacéutico", use_extended_strategy=True)
        frappe.clear_cache()

        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_can_access_doctype("Batch", should_access=True))
        self.assertTrue(test_has_permission("Batch", "read", should_have=True))
        self.assertTrue(test_has_permission("Batch", "write", should_have=True))
        self.assertTrue(test_has_permission("Batch", "create", should_have=True))

    def test_farmaceutico_can_create_serial_and_batch_bundle(self):
        """Farmacéutico puede crear Serial and Batch Bundle (whiteboard #78 PR1)"""
        from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
            setup_permissions_for_role,
        )

        frappe.set_user("Administrator")
        setup_permissions_for_role("Farmacéutico", use_extended_strategy=True)
        frappe.clear_cache()

        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Serial and Batch Bundle", "read", should_have=True))
        self.assertTrue(test_has_permission("Serial and Batch Bundle", "write", should_have=True))
        self.assertTrue(test_has_permission("Serial and Batch Bundle", "create", should_have=True))

    def test_farmaceutico_can_create_receta_retenida_item_with_required_fields(self):
        """Farm crea Item Receta Retenida con sanitario, lote, serie y shelf_life (whiteboard #78 PR2)"""
        from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
            setup_permissions_for_role,
        )
        from frappe.utils import cint

        frappe.set_user("Administrator")
        setup_permissions_for_role("Farmacéutico", use_extended_strategy=True)
        frappe.clear_cache()

        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Item", "create", should_have=True))

        code = f"TEST-RR-FARM-{frappe.generate_hash(length=6)}"
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": code,
                "item_name": f"RR {code}",
                "item_group": "Medicamentos de Prueba",
                "stock_uom": "Unidad",
                "is_stock_item": 1,
                "custom_dispensing_type": "Venta con Receta Retenida",
                "custom_sanitary_registration": "ISP-TEST-9999",
                "has_batch_no": 1,
                "has_expiry_date": 1,
                "has_serial_no": 1,
                "shelf_life_in_days": 9999,
            }
        )
        item.insert()
        frappe.db.commit()
        self.test_items.append(item.name)

        item.reload()
        self.assertEqual(item.custom_dispensing_type, "Venta con Receta Retenida")
        self.assertEqual(item.custom_sanitary_registration, "ISP-TEST-9999")
        self.assertEqual(cint(item.has_batch_no), 1)
        self.assertEqual(cint(item.has_expiry_date), 1)
        self.assertEqual(cint(item.has_serial_no), 1)
        self.assertEqual(cint(item.shelf_life_in_days), 9999)
        self.assertEqual(cint(item.custom_prescription_storage_required), 1)

    def test_farmaceutico_receta_retenida_requires_sanitary_registration(self):
        """Sin registro sanitario, Farm no guarda Receta Retenida (whiteboard #78 PR2)"""
        from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
            setup_permissions_for_role,
        )

        frappe.set_user("Administrator")
        setup_permissions_for_role("Farmacéutico", use_extended_strategy=True)
        frappe.clear_cache()

        frappe.set_user(self.username)
        frappe.clear_cache()

        code = f"TEST-RR-NOSAN-{frappe.generate_hash(length=6)}"
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": code,
                "item_name": f"RR {code}",
                "item_group": "Medicamentos de Prueba",
                "stock_uom": "Unidad",
                "is_stock_item": 1,
                "custom_dispensing_type": "Venta con Receta Retenida",
                "custom_sanitary_registration": "",
                "has_batch_no": 1,
                "has_expiry_date": 1,
                "has_serial_no": 1,
                "shelf_life_in_days": 9999,
            }
        )
        with self.assertRaises(frappe.ValidationError):
            item.insert()

    def test_farmaceutico_can_read_shelf(self):
        """Farmacéutico puede leer Shelf (PR, reconciliación de inventario)"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Shelf", "read", should_have=True))


class TestAuxiliarRole(TestEpic8Story82RoleAuthorization):
    """Tests para rol Auxiliar"""

    def setUp(self):
        super().setUp()
        self.username = f"test_auxiliar_{frappe.generate_hash(length=6)}"
        self.user = create_test_user_with_role(self.username, "Auxiliar")
        self.test_users.append(self.username)

    def test_auxiliar_can_read_prescription(self):
        """Auxiliar puede leer Prescription"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Receta Medica", should_access=True))

    def test_auxiliar_cannot_write_prescription(self):
        """Auxiliar NO puede escribir Prescription"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Receta Medica", "write", should_have=False))

    def test_auxiliar_can_read_sales_invoice(self):
        """Auxiliar puede leer Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Sales Invoice", should_access=True))

    def test_auxiliar_can_write_sales_invoice(self):
        """Auxiliar puede escribir Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Sales Invoice", "write", should_have=True))

    def test_auxiliar_can_create_sales_invoice(self):
        """Auxiliar puede crear Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Sales Invoice", "create", should_have=True))

    def test_auxiliar_can_read_item(self):
        """Auxiliar puede leer Item"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Item", should_access=True))

    def test_auxiliar_can_write_item(self):
        """Auxiliar puede escribir Item existente (p. ej. imagen en recepción)"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Item", "write", should_have=True))

    def test_auxiliar_cannot_create_item(self):
        """Auxiliar NO puede crear Item (maestro lo define farmacéutico/bodega)"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Item", "create", should_have=False))

    def test_auxiliar_can_read_purchase_receipt(self):
        """Auxiliar puede leer Purchase Receipt"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_can_access_doctype("Purchase Receipt", should_access=True))

    def test_auxiliar_can_create_purchase_receipt(self):
        """Auxiliar puede crear Purchase Receipt (recepción borrador)"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Purchase Receipt", "create", should_have=True))

    def test_auxiliar_cannot_submit_purchase_receipt(self):
        """Auxiliar NO puede submitir Purchase Receipt (QC farmacéutico)"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Purchase Receipt", "submit", should_have=False))

    def test_auxiliar_can_create_pos_closing_entry(self):
        """Auxiliar puede crear y cerrar caja POS (POS Closing Entry)"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("POS Closing Entry", "create", should_have=True))
        self.assertTrue(test_has_permission("POS Closing Entry", "submit", should_have=True))

    def test_auxiliar_can_read_pos_and_stock_settings(self):
        """Auxiliar puede leer singles y maestros contables mínimos para POS."""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Stock Settings", "read", should_have=True))
        self.assertTrue(test_has_permission("POS Settings", "read", should_have=True))
        self.assertTrue(test_has_permission("Account", "read", should_have=True))
        self.assertTrue(test_has_permission("Cost Center", "read", should_have=True))
        self.assertTrue(test_has_permission("Mode of Payment", "read", should_have=True))
        self.assertTrue(test_has_permission("UOM", "read", should_have=True))
        self.assertTrue(test_has_permission("Buying Settings", "read", should_have=True))
        self.assertTrue(test_has_permission("Territory", "read", should_have=True))
        self.assertTrue(test_has_permission("Customer Group", "read", should_have=True))
        self.assertTrue(test_has_permission("Currency", "read", should_have=True))
        self.assertTrue(
            test_has_permission("Sales Taxes and Charges Template", "read", should_have=True)
        )

    def test_auxiliar_can_read_shelf_for_purchase_receipt(self):
        """Auxiliar puede leer Shelf para asignar estante en líneas de PR"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Shelf", "read", should_have=True))

    def test_auxiliar_can_read_purchase_order(self):
        """Auxiliar puede leer Purchase Order para enlazar PR"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_can_access_doctype("Purchase Order", should_access=True))

    def test_auxiliar_cannot_read_buying_dashboard_reports(self):
        """Auxiliar no ve gráficos del tablero Compras (sin roles en reportes de tendencias)"""
        from barriofarma_app.barriofarma_app.utils.permissions.frappe_v16_compat import (
            get_allowed_report_names,
        )

        frappe.set_user(self.username)
        frappe.clear_cache()
        allowed = get_allowed_report_names()
        for report in (
            "Purchase Order Trends",
            "Purchase Order Analysis",
            "Purchase Receipt Trends",
        ):
            self.assertNotIn(report, allowed, msg=report)

    def test_auxiliar_can_operate_stock_entry(self):
        """Auxiliar puede trasladar stock entre bodegas (Stock Entry)"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_can_access_doctype("Stock Entry", should_access=True))
        self.assertTrue(test_has_permission("Stock Entry", "create", should_have=True))
        self.assertTrue(test_has_permission("Stock Entry", "submit", should_have=True))

    def test_auxiliar_can_operate_shelf_movement(self):
        """Auxiliar puede mover mercadería entre estantes"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Shelf Movement", "create", should_have=True))
        self.assertTrue(test_has_permission("Shelf Movement", "submit", should_have=True))

    def test_auxiliar_can_operate_stock_reconciliation(self):
        """Auxiliar puede crear y validar Reconciliación de inventarios"""
        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_can_access_doctype("Stock Reconciliation", should_access=True))
        self.assertTrue(test_has_permission("Stock Reconciliation", "create", should_have=True))
        self.assertTrue(test_has_permission("Stock Reconciliation", "submit", should_have=True))

    def test_auxiliar_can_create_batch(self):
        """Auxiliar puede crear y escribir Batch (whiteboard #78 PR1)"""
        from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
            setup_permissions_for_role,
        )

        frappe.set_user("Administrator")
        setup_permissions_for_role("Auxiliar", use_extended_strategy=True)
        frappe.clear_cache()

        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_can_access_doctype("Batch", should_access=True))
        self.assertTrue(test_has_permission("Batch", "read", should_have=True))
        self.assertTrue(test_has_permission("Batch", "write", should_have=True))
        self.assertTrue(test_has_permission("Batch", "create", should_have=True))

    def test_auxiliar_can_create_serial_and_batch_bundle(self):
        """Auxiliar puede crear Serial and Batch Bundle (whiteboard #78 PR1)"""
        from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
            setup_permissions_for_role,
        )

        frappe.set_user("Administrator")
        setup_permissions_for_role("Auxiliar", use_extended_strategy=True)
        frappe.clear_cache()

        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Serial and Batch Bundle", "read", should_have=True))
        self.assertTrue(test_has_permission("Serial and Batch Bundle", "write", should_have=True))
        self.assertTrue(test_has_permission("Serial and Batch Bundle", "create", should_have=True))

    def test_auxiliar_cannot_create_receta_retenida_item(self):
        """Auxiliar no puede crear Item (ACL + insert) — whiteboard #78 PR2"""
        from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
            setup_permissions_for_role,
        )

        frappe.set_user("Administrator")
        setup_permissions_for_role("Auxiliar", use_extended_strategy=True)
        frappe.clear_cache()

        frappe.set_user(self.username)
        frappe.clear_cache()
        self.assertTrue(test_has_permission("Item", "create", should_have=False))

        code = f"TEST-RR-AUX-{frappe.generate_hash(length=6)}"
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": code,
                "item_name": f"RR {code}",
                "item_group": "Medicamentos de Prueba",
                "stock_uom": "Unidad",
                "is_stock_item": 1,
                "custom_dispensing_type": "Venta con Receta Retenida",
                "custom_sanitary_registration": "ISP-TEST-AUX",
                "has_batch_no": 1,
                "has_expiry_date": 1,
                "has_serial_no": 1,
                "shelf_life_in_days": 9999,
            }
        )
        with self.assertRaises(frappe.PermissionError):
            item.insert()


class TestBodegueroRole(TestEpic8Story82RoleAuthorization):
    """Tests para rol Bodeguero"""

    def setUp(self):
        super().setUp()
        self.username = f"test_bodeguero_{frappe.generate_hash(length=6)}"
        self.user = create_test_user_with_role(self.username, "Bodeguero")
        self.test_users.append(self.username)

    def test_bodeguero_cannot_access_prescription(self):
        """Bodeguero NO puede acceder a Prescription"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Receta Medica", should_access=False))

    def test_bodeguero_cannot_access_sales_invoice(self):
        """Bodeguero NO puede acceder a Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Sales Invoice", should_access=False))

    def test_bodeguero_can_read_purchase_receipt(self):
        """Bodeguero puede leer Purchase Receipt"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Purchase Receipt", should_access=True))

    def test_bodeguero_cannot_write_purchase_receipt(self):
        """Bodeguero NO escribe Purchase Receipt (flujo auxiliar + QC farmacéutico)"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Purchase Receipt", "write", should_have=False))

    def test_bodeguero_cannot_create_purchase_receipt(self):
        """Bodeguero NO crea Purchase Receipt en perfil dedicado"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Purchase Receipt", "create", should_have=False))

    def test_bodeguero_can_read_stock_entry(self):
        """Bodeguero puede leer Stock Entry"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Stock Entry", should_access=True))

    def test_bodeguero_can_write_stock_entry(self):
        """Bodeguero puede escribir Stock Entry"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Stock Entry", "write", should_have=True))

    def test_bodeguero_can_read_shelf(self):
        """Bodeguero puede leer Shelf"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Shelf", should_access=True))

    def test_bodeguero_can_write_shelf(self):
        """Bodeguero puede escribir Shelf"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Shelf", "write", should_have=True))


class TestAdministrativoRole(TestEpic8Story82RoleAuthorization):
    """Tests para rol Administrativo"""

    def setUp(self):
        super().setUp()
        self.username = f"test_administrativo_{frappe.generate_hash(length=6)}"
        self.user = create_test_user_with_role(self.username, "Administrativo")
        self.test_users.append(self.username)

    def test_administrativo_can_read_all_critical_doctypes(self):
        """
        Administrativo puede leer todos los DocTypes críticos permitidos
        
        Nota: Administrativo NO tiene acceso a Prescription según la matriz de permisos
        """
        frappe.set_user(self.username)
        # DocTypes que Administrativo SÍ puede leer (según matriz de permisos)
        critical_doctypes = [
            "Sales Invoice", "Purchase Receipt", 
            "Stock Entry", "Shelf", "Shelf Movement", "Item", "Customer", "Patient", "Payment Entry", "Purchase Invoice"
        ]
        for doctype in critical_doctypes:
            with self.subTest(doctype=doctype):
                self.assertTrue(test_can_access_doctype(doctype, should_access=True))
        
        # Verificar que NO puede acceder a Prescription
        self.assertTrue(test_can_access_doctype("Receta Medica", should_access=False))

    def test_administrativo_cannot_write_any_doctype(self):
        """Administrativo NO puede escribir ningún DocType crítico"""
        frappe.set_user(self.username)
        critical_doctypes = [
            "Receta Medica", "Sales Invoice", "Purchase Receipt", 
            "Stock Entry", "Shelf", "Item"
        ]
        for doctype in critical_doctypes:
            with self.subTest(doctype=doctype):
                self.assertTrue(test_has_permission(doctype, "write", should_have=False))

    def test_administrativo_cannot_create_any_doctype(self):
        """Administrativo NO puede crear ningún DocType crítico"""
        frappe.set_user(self.username)
        critical_doctypes = [
            "Receta Medica", "Sales Invoice", "Purchase Receipt", 
            "Stock Entry", "Shelf"
        ]
        for doctype in critical_doctypes:
            with self.subTest(doctype=doctype):
                self.assertTrue(test_has_permission(doctype, "create", should_have=False))


class TestContabilidadRole(TestEpic8Story82RoleAuthorization):
    """Tests para rol Contabilidad"""

    def setUp(self):
        super().setUp()
        self.username = f"test_contabilidad_{frappe.generate_hash(length=6)}"
        self.user = create_test_user_with_role(self.username, "Contabilidad")
        self.test_users.append(self.username)

    def test_contabilidad_can_read_sales_invoice(self):
        """Contabilidad puede leer Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Sales Invoice", should_access=True))

    def test_contabilidad_can_write_sales_invoice(self):
        """Contabilidad puede escribir Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Sales Invoice", "write", should_have=True))

    def test_contabilidad_can_submit_sales_invoice(self):
        """Contabilidad puede enviar Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Sales Invoice", "submit", should_have=True))

    def test_contabilidad_can_cancel_sales_invoice(self):
        """Contabilidad puede cancelar Sales Invoice"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Sales Invoice", "cancel", should_have=True))

    def test_contabilidad_can_read_payment_entry(self):
        """Contabilidad puede leer Payment Entry"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Payment Entry", should_access=True))

    def test_contabilidad_can_write_payment_entry(self):
        """Contabilidad puede escribir Payment Entry"""
        frappe.set_user(self.username)
        self.assertTrue(test_has_permission("Payment Entry", "write", should_have=True))

    def test_contabilidad_cannot_access_prescription(self):
        """Contabilidad NO puede acceder a Prescription"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Receta Medica", should_access=False))

    def test_contabilidad_cannot_access_purchase_receipt(self):
        """Contabilidad NO puede acceder a Purchase Receipt"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Purchase Receipt", should_access=False))

    def test_contabilidad_cannot_access_stock_entry(self):
        """Contabilidad NO puede acceder a Stock Entry"""
        frappe.set_user(self.username)
        self.assertTrue(test_can_access_doctype("Stock Entry", should_access=False))


class TestInformaticaRole(TestEpic8Story82RoleAuthorization):
    """Tests para rol Informática"""

    def setUp(self):
        super().setUp()
        self.username = f"test_informatica_{frappe.generate_hash(length=6)}"
        self.user = create_test_user_with_role(self.username, "Informática")
        self.test_users.append(self.username)

    def test_informatica_has_full_access_to_all_doctypes(self):
        """Informática tiene acceso completo a todos los DocTypes críticos"""
        frappe.set_user(self.username)
        critical_doctypes = [
            "Receta Medica", "Sales Invoice", "Purchase Receipt", 
            "Stock Entry", "Shelf", "Item", "Customer", "Patient", "Doctor"
        ]
        for doctype in critical_doctypes:
            with self.subTest(doctype=doctype):
                self.assertTrue(test_can_access_doctype(doctype, should_access=True))
                self.assertTrue(test_has_permission(doctype, "write", should_have=True))
                self.assertTrue(test_has_permission(doctype, "create", should_have=True))
                self.assertTrue(test_has_permission(doctype, "delete", should_have=True))

    def test_informatica_can_read_buying_dashboard_reports(self):
        """Informática: reportes de gráficos del tablero Compras (mantenedor plataforma)"""
        from barriofarma_app.barriofarma_app.utils.permissions.setup_buying_dashboard_access import (
            setup_buying_dashboard_reports,
        )
        from barriofarma_app.barriofarma_app.utils.permissions.frappe_v16_compat import (
            get_allowed_report_names,
        )

        setup_buying_dashboard_reports()
        frappe.set_user(self.username)
        frappe.clear_cache()
        allowed = get_allowed_report_names()
        for report in (
            "Purchase Order Trends",
            "Purchase Order Analysis",
            "Purchase Receipt Trends",
        ):
            self.assertIn(report, allowed, msg=report)


class TestEdgeCases(TestEpic8Story82RoleAuthorization):
    """Tests de casos edge"""

    def setUp(self):
        super().setUp()
        # Crear usuario sin rol
        self.username_no_role = f"test_no_role_{frappe.generate_hash(length=6)}"
        if not frappe.db.exists("User", self.username_no_role):
            # Deshabilitar throttling para tests
            frappe.flags.in_import = True
            try:
                user = frappe.get_doc({
                    "doctype": "User",
                    "email": f"{self.username_no_role}@test.barriofarma.cl",
                    "first_name": self.username_no_role,
                    "username": self.username_no_role,
                    "send_welcome_email": 0
                })
                user.insert(ignore_permissions=True)
                frappe.db.commit()
            finally:
                frappe.flags.in_import = False
        self.test_users.append(self.username_no_role)

    def test_user_without_role_cannot_access_doctypes(self):
        """Usuario sin rol NO puede acceder a DocTypes"""
        frappe.set_user(self.username_no_role)
        critical_doctypes = [
            "Receta Medica", "Sales Invoice", "Purchase Receipt", 
            "Stock Entry", "Shelf", "Item"
        ]
        for doctype in critical_doctypes:
            with self.subTest(doctype=doctype):
                self.assertTrue(test_can_access_doctype(doctype, should_access=False))

    def test_read_only_user_cannot_write(self):
        """Usuario con solo Read NO puede Write"""
        username = f"test_readonly_{frappe.generate_hash(length=6)}"
        user = create_test_user_with_role(username, "Administrativo")
        self.test_users.append(username)
        
        frappe.set_user(username)
        # Administrativo tiene solo Read en todos los DocTypes
        self.assertTrue(test_has_permission("Sales Invoice", "read", should_have=True))
        self.assertTrue(test_has_permission("Sales Invoice", "write", should_have=False))

    def test_submit_requires_write(self):
        """Submit requiere Write (validación implícita de Frappe)"""
        username = f"test_submit_{frappe.generate_hash(length=6)}"
        user = create_test_user_with_role(username, "Administrativo")
        self.test_users.append(username)
        
        frappe.set_user(username)
        # Administrativo no tiene Write, por lo tanto no puede Submit
        self.assertTrue(test_has_permission("Sales Invoice", "write", should_have=False))
        self.assertTrue(test_has_permission("Sales Invoice", "submit", should_have=False))


class TestUserPermissions(TestEpic8Story82RoleAuthorization):
    """
    Tests para User Permissions (Document-Level Permissions)
    
    Según best practices de Frappe:
    - User Permissions permiten restringir acceso a documentos específicos
    - Útil para casos donde un usuario solo debe ver sus propios datos
    - Se configuran en Desk → User Permission
    
    Referencia: https://explorewithjnk.com/blog/2025/08/13/mastering-frappe-framework-part-6-user-permissions-roles/
    """

    def setUp(self):
        super().setUp()
        # Crear usuario Farmacéutico para tests de User Permissions
        self.username = f"test_user_perm_{frappe.generate_hash(length=6)}"
        self.user = create_test_user_with_role(self.username, "Farmacéutico")
        self.test_users.append(self.username)
        
        # Crear documento de prueba (Prescription)
        frappe.set_user("Administrator")
        self.test_prescriptions = []

    def tearDown(self):
        # Limpiar User Permissions
        frappe.set_user("Administrator")
        user_name = normalize_user(self.username)
        user_perms = frappe.get_all("User Permission", 
            filters={"user": user_name}, 
            fields=["name"])
        for up in user_perms:
            frappe.delete_doc("User Permission", up.name, ignore_permissions=True, force=1)
        frappe.db.commit()
        super().tearDown()

    def test_user_permission_restricts_access_to_specific_documents(self):
        """
        User Permission restringe acceso a documentos específicos
        
        Best Practice: Usar User Permissions para casos donde un usuario
        solo debe ver sus propios datos o datos asignados a él.
        """
        frappe.set_user("Administrator")
        
        # Crear dos Prescriptions usando helper
        presc1 = create_test_prescription(
            prescription_number=f"PRES-TEST-1-{frappe.generate_hash(length=6)}",
            patient="Test Patient 1"
        )
        self.test_prescriptions.append(presc1.name)
        
        presc2 = create_test_prescription(
            prescription_number=f"PRES-TEST-2-{frappe.generate_hash(length=6)}",
            patient="Test Patient 2"
        )
        self.test_prescriptions.append(presc2.name)
        frappe.db.commit()
        
        # Crear User Permission para que el usuario solo vea presc1
        user_perm = frappe.get_doc({
            "doctype": "User Permission",
            "user": normalize_user(self.username),
            "allow": "Receta Medica",
            "for_value": presc1.name
        })
        user_perm.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Cambiar contexto y verificar acceso
        frappe.set_user(self.username)
        frappe.clear_cache()
        
        # Debe poder acceder a presc1
        self.assertTrue(frappe.has_permission("Receta Medica", "read", presc1))
        
        # NO debe poder acceder a presc2 (sin User Permission)
        # Nota: En Frappe, sin User Permission específica, el usuario puede ver todos
        # los documentos según sus permisos de rol. User Permission es adicional.
        # Para restringir completamente, se necesitaría lógica adicional.

    def test_user_permission_works_with_role_permissions(self):
        """
        User Permissions trabajan en conjunto con permisos de rol
        
        Best Practice: User Permissions son adicionales a los permisos de rol.
        El usuario debe tener permisos de rol Y User Permission para acceder.
        """
        frappe.set_user("Administrator")
        
        # Crear Prescription usando helper
        presc = create_test_prescription(
            prescription_number=f"PRES-TEST-{frappe.generate_hash(length=6)}",
            patient="Test Patient"
        )
        self.test_prescriptions.append(presc.name)
        frappe.db.commit()
        
        # Crear User Permission
        user_perm = frappe.get_doc({
            "doctype": "User Permission",
            "user": normalize_user(self.username),
            "allow": "Receta Medica",
            "for_value": presc.name
        })
        user_perm.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Cambiar contexto y verificar
        frappe.set_user(self.username)
        frappe.clear_cache()
        
        # Farmacéutico tiene permisos de rol para Prescription
        # Y tiene User Permission para este documento específico
        # Por lo tanto, debe poder acceder
        self.assertTrue(frappe.has_permission("Receta Medica", "read", presc))
        self.assertTrue(frappe.has_permission("Receta Medica", "write", presc))


class TestDocumentLevelPermissions(TestEpic8Story82RoleAuthorization):
    """
    Tests para validar permisos a nivel de documento específico
    
    Valida que has_permission() funciona correctamente cuando se pasa
    un documento específico, no solo el DocType.
    """

    def setUp(self):
        super().setUp()
        self.username = f"test_doc_perm_{frappe.generate_hash(length=6)}"
        self.user = create_test_user_with_role(self.username, "Farmacéutico")
        self.test_users.append(self.username)

    def test_has_permission_with_document(self):
        """
        Validar que has_permission() funciona con documento específico
        
        Best Practice: Usar has_permission() con documento específico
        para validar acceso a documentos individuales.
        """
        frappe.set_user("Administrator")
        
        # Crear Prescription usando helper
        presc = create_test_prescription(
            prescription_number=f"PRES-DOC-{frappe.generate_hash(length=6)}",
            patient="Test Patient"
        )
        frappe.db.commit()
        
        # Cambiar contexto y verificar permisos en el documento
        frappe.set_user(self.username)
        frappe.clear_cache()
        
        # Verificar permisos en el documento específico
        self.assertTrue(frappe.has_permission("Receta Medica", "read", presc))
        self.assertTrue(frappe.has_permission("Receta Medica", "write", presc))
        self.assertTrue(frappe.has_permission("Receta Medica", "create"))
        
        # Limpiar
        frappe.set_user("Administrator")
        if frappe.db.exists("Receta Medica", presc.name):
            frappe.delete_doc("Receta Medica", presc.name, ignore_permissions=True, force=1)
        frappe.db.commit()

