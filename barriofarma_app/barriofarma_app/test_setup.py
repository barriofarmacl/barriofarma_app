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

