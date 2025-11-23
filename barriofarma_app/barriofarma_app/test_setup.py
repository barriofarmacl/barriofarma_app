# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Helpers de setup para tests de BarrioFarma
Disponibles para crear datos mínimos en español
"""

import frappe


def ensure_minimum_masters():
    """
    Asegura que existan los masters mínimos necesarios para tests:
    - UOM "Unidad"
    - Item Group "Medicamentos de Prueba"
    """
    # UOM "Unidad"
    if not frappe.db.exists("UOM", "Unidad"):
        uom = frappe.get_doc({
            "doctype": "UOM",
            "uom_name": "Unidad"
        })
        uom.insert(ignore_permissions=True)
        frappe.db.commit()
    
    # Item Group "Medicamentos de Prueba"
    if not frappe.db.exists("Item Group", "Medicamentos de Prueba"):
        item_group = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": "Medicamentos de Prueba",
            "is_group": 0
        })
        item_group.insert(ignore_permissions=True)
        frappe.db.commit()


def get_or_create_root_customer_group():
    """Crea/usa Customer Group raíz en ES/EN"""
    customer_group_name = frappe.db.get_value("Customer Group", {"is_group": 1}, "name")
    if not customer_group_name:
        customer_group = frappe.get_doc({
            "doctype": "Customer Group",
            "customer_group_name": "All Customer Groups",
            "is_group": 1
        })
        customer_group.insert(ignore_permissions=True)
        frappe.db.commit()
        return customer_group.name
    return customer_group_name


def get_or_create_root_territory():
    """Crea/usa Territory raíz en ES/EN"""
    territory_name = frappe.db.get_value("Territory", {"is_group": 1}, "name")
    if not territory_name:
        territory = frappe.get_doc({
            "doctype": "Territory",
            "territory_name": "All Territories",
            "is_group": 1
        })
        territory.insert(ignore_permissions=True)
        frappe.db.commit()
        return territory.name
    return territory_name


def create_test_customer(customer_name, customer_type="Individual", **kwargs):
    """
    Función auxiliar para crear Customer de prueba
    
    Args:
        customer_name: Nombre del cliente
        customer_type: Tipo de cliente (Individual/Company)
        **kwargs: Campos adicionales del Customer
    
    Returns:
        Customer document creado
    """
    if frappe.db.exists("Customer", customer_name):
        return frappe.get_doc("Customer", customer_name)
    
    customer_group = get_or_create_root_customer_group()
    territory = get_or_create_root_territory()
    
    defaults = {
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_type": customer_type,
        "customer_group": customer_group,
        "territory": territory,
    }
    
    defaults.update(kwargs)
    
    customer = frappe.get_doc(defaults)
    customer.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return customer


def get_or_create_item_group(item_group_name="Products"):
    """
    Obtiene o crea un Item Group
    
    Args:
        item_group_name: Nombre del Item Group
    
    Returns:
        Nombre del Item Group
    """
    if frappe.db.exists("Item Group", item_group_name):
        return item_group_name
    
    item_group = frappe.get_doc({
        "doctype": "Item Group",
        "item_group_name": item_group_name,
        "is_group": 0
    })
    item_group.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return item_group_name


def get_or_create_uom(uom_name="Nos"):
    """
    Obtiene o crea una UOM (Unidad de Medida)
    
    Args:
        uom_name: Nombre de la UOM
    
    Returns:
        Nombre de la UOM
    """
    if frappe.db.exists("UOM", uom_name):
        return uom_name
    
    uom = frappe.get_doc({
        "doctype": "UOM",
        "uom_name": uom_name
    })
    uom.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return uom_name


def create_test_item(**kwargs):
    """
    Función auxiliar para crear Item de prueba
    
    Args:
        **kwargs: Campos del Item a crear
    
    Returns:
        Item document creado
    """
    ensure_minimum_masters()
    
    # Valores por defecto
    defaults = {
        "doctype": "Item",
        "item_code": kwargs.get("item_code", f"TEST-ITEM-{frappe.generate_hash(length=8)}"),
        "item_name": kwargs.get("item_name", "Producto de Prueba"),
        "item_group": kwargs.get("item_group", "Medicamentos de Prueba"),
        "stock_uom": kwargs.get("stock_uom", "Unidad"),
        "is_stock_item": kwargs.get("is_stock_item", 1),
        "has_batch_no": kwargs.get("has_batch_no", 0),
        "has_expiry_date": kwargs.get("has_expiry_date", 0),
    }
    
    # Actualizar con valores pasados
    defaults.update(kwargs)
    
    item = frappe.get_doc(defaults)
    item.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return item


def create_test_supplier(supplier_name, **kwargs):
    """
    Función auxiliar para crear Supplier de prueba
    
    Args:
        supplier_name: Nombre del proveedor
        **kwargs: Campos adicionales del Supplier
    
    Returns:
        Supplier document creado
    """
    if frappe.db.exists("Supplier", supplier_name):
        return frappe.get_doc("Supplier", supplier_name)
    
    defaults = {
        "doctype": "Supplier",
        "supplier_name": supplier_name,
        "supplier_type": kwargs.get("supplier_type", "Company"),
    }
    
    defaults.update(kwargs)
    
    supplier = frappe.get_doc(defaults)
    supplier.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return supplier


def create_test_warehouse(warehouse_name, **kwargs):
    """
    Función auxiliar para crear Warehouse de prueba
    
    Args:
        warehouse_name: Nombre del warehouse
        **kwargs: Campos adicionales del Warehouse
    
    Returns:
        Warehouse document creado
    """
    if frappe.db.exists("Warehouse", warehouse_name):
        return frappe.get_doc("Warehouse", warehouse_name)
    
    # Obtener o crear Company por defecto - Siempre usar Barriofarma (CLP) para tests
    company = kwargs.get("company")
    if not company:
        # Primero intentar usar Barriofarma (company real con CLP)
        if frappe.db.exists("Company", "Barriofarma"):
            company = "Barriofarma"
        else:
            # Fallback: cualquier company con CLP
            company = frappe.db.get_value("Company", {"default_currency": "CLP"}, "name")
            if not company:
                # Crear company básica con CLP si no existe
                company = frappe.get_doc({
                    "doctype": "Company",
                    "company_name": "Barriofarma Test",
                    "abbr": "BFT",
                    "default_currency": "CLP",
                    "country": "Chile"
                })
                company.insert(ignore_permissions=True)
                frappe.db.commit()
                company = company.name
    
    defaults = {
        "doctype": "Warehouse",
        "warehouse_name": warehouse_name,
        "company": company,
    }
    
    defaults.update(kwargs)
    
    warehouse = frappe.get_doc(defaults)
    warehouse.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return warehouse


def create_test_purchase_order(item_code, qty, supplier_name=None, **kwargs):
    """
    Función auxiliar para crear Purchase Order de prueba
    
    Args:
        item_code: Código del ítem a comprar
        qty: Cantidad a comprar
        supplier_name: Nombre del proveedor (se crea si no existe)
        **kwargs: Campos adicionales del Purchase Order
    
    Returns:
        Purchase Order document creado
    """
    # Crear supplier si no existe
    if not supplier_name:
        supplier_name = f"TEST-SUPPLIER-{frappe.generate_hash(length=6)}"
    
    supplier = create_test_supplier(supplier_name)
    
    # Obtener company - Siempre usar Barriofarma (CLP) para tests
    company = kwargs.get("company")
    if not company:
        # Primero intentar usar Barriofarma (company real con CLP)
        if frappe.db.exists("Company", "Barriofarma"):
            company = "Barriofarma"
        else:
            # Fallback: cualquier company con CLP
            company = frappe.db.get_value("Company", {"default_currency": "CLP"}, "name")
            if not company:
                # Último recurso: cualquier company disponible
                company = frappe.db.get_value("Company", {"name": ("!=", "")}, "name")
    
    # Obtener item
    if not frappe.db.exists("Item", item_code):
        raise ValueError(f"Item {item_code} no existe. Crear primero con create_test_item.")
    
    item = frappe.get_doc("Item", item_code)
    
    defaults = {
        "doctype": "Purchase Order",
        "supplier": supplier.name,
        "company": company,
        "transaction_date": kwargs.get("transaction_date", frappe.utils.today()),
        "schedule_date": kwargs.get("schedule_date", frappe.utils.add_days(frappe.utils.today(), 7)),
        "items": [{
            "item_code": item_code,
            "qty": qty,
            "uom": item.stock_uom,
            "rate": kwargs.get("rate", 100),
            "schedule_date": kwargs.get("schedule_date", frappe.utils.add_days(frappe.utils.today(), 7)),
        }]
    }
    
    defaults.update({k: v for k, v in kwargs.items() if k not in ["company", "transaction_date", "rate"]})
    
    po = frappe.get_doc(defaults)
    po.insert(ignore_permissions=True)
    po.submit()
    frappe.db.commit()
    
    return po


def create_test_batch(item_code, batch_id, expiry_date, **kwargs):
	"""
	Función auxiliar para crear Batch de prueba
	
	Args:
		item_code: Código del ítem
		batch_id: ID del lote
		expiry_date: Fecha de vencimiento (YYYY-MM-DD)
		**kwargs: Campos adicionales del Batch
	
	Returns:
		Batch document creado
	"""
	if frappe.db.exists("Batch", batch_id):
		return frappe.get_doc("Batch", batch_id)
	
	# Validar que el item requiere batch
	item = frappe.get_doc("Item", item_code)
	if not item.has_batch_no:
		raise ValueError(f"Item {item_code} no requiere gestión por lote (has_batch_no=0)")
	
	defaults = {
		"doctype": "Batch",
		"batch_id": batch_id,
		"item": item_code,
		"expiry_date": expiry_date,
	}
	
	defaults.update(kwargs)
	
	batch = frappe.get_doc(defaults)
	batch.insert(ignore_permissions=True)
	frappe.db.commit()
	
	return batch


def create_test_doctor(doctor_name=None, license_number=None, **kwargs):
	"""
	Función auxiliar para crear Doctor de prueba
	
	Args:
		doctor_name: Nombre completo del médico (si no se proporciona, se genera uno)
		license_number: Número de licencia médica (si no se proporciona, se genera uno único)
		**kwargs: Campos adicionales del Doctor (specialty, contact_info, etc.)
	
	Returns:
		Doctor document creado
	"""
	# Generar valores por defecto si no se proporcionan
	if not doctor_name:
		doctor_name = f"Dr. Test Médico {frappe.generate_hash(length=6)}"
	
	if not license_number:
		license_number = f"TEST-LIC-{frappe.generate_hash(length=8)}"
	
	# Verificar si ya existe un doctor con esta licencia
	existing_doctor = frappe.db.get_value("Doctor", {"license_number": license_number}, "name")
	if existing_doctor:
		return frappe.get_doc("Doctor", existing_doctor)
	
	defaults = {
		"doctype": "Doctor",
		"doctor_name": doctor_name,
		"license_number": license_number,
		"specialty": kwargs.get("specialty"),
		"contact_info": kwargs.get("contact_info"),
	}
	
	# Remover None values
	defaults = {k: v for k, v in defaults.items() if v is not None}
	
	doctor = frappe.get_doc(defaults)
	doctor.insert(ignore_permissions=True)
	frappe.db.commit()
	
	return doctor


def create_test_patient(patient_name=None, rut_dni=None, **kwargs):
	"""
	Función auxiliar para crear Patient de prueba
	
	Args:
		patient_name: Nombre completo del paciente (si no se proporciona, se genera uno)
		rut_dni: RUT/DNI del paciente (si no se proporciona, se genera uno único)
		**kwargs: Campos adicionales del Patient (date_of_birth, gender, etc.)
	
	Returns:
		Patient document creado
	"""
	# Generar valores por defecto si no se proporcionan
	if not patient_name:
		patient_name = f"Paciente Test {frappe.generate_hash(length=6)}"
	
	if not rut_dni:
		rut_dni = f"TEST-RUT-{frappe.generate_hash(length=8)}"
	
	# Verificar si ya existe un paciente con este RUT
	existing_patient = frappe.db.get_value("Patient", {"rut_dni": rut_dni}, "name")
	if existing_patient:
		return frappe.get_doc("Patient", existing_patient)
	
	defaults = {
		"doctype": "Patient",
		"patient_name": patient_name,
		"rut_dni": rut_dni,
		"date_of_birth": kwargs.get("date_of_birth"),
		"gender": kwargs.get("gender"),
		"address": kwargs.get("address"),
		"phone": kwargs.get("phone"),
		"email": kwargs.get("email"),
		"blood_group": kwargs.get("blood_group"),
		"allergies": kwargs.get("allergies"),
		"medical_conditions": kwargs.get("medical_conditions"),
	}
	
	# Remover None values
	defaults = {k: v for k, v in defaults.items() if v is not None}
	
	patient = frappe.get_doc(defaults)
	patient.insert(ignore_permissions=True)
	frappe.db.commit()
	
	return patient

