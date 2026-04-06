# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Script para analizar roles y permisos existentes en el sistema
Story 8.1: Refinamiento de Gestión de Usuarios y Roles
"""

import frappe


def list_all_roles():
    """Listar todos los roles existentes en el sistema"""
    roles = frappe.get_all(
        "Role",
        fields=["name", "desk_access", "is_custom", "disabled"],
        order_by="name"
    )
    
    print("\n=== Roles Existentes en el Sistema ===\n")
    print(f"Total de roles: {len(roles)}\n")
    
    for role in roles:
        custom = "Sí" if role.get("is_custom") else "No"
        disabled = "Sí" if role.get("disabled") else "No"
        desk_access = "Sí" if role.get("desk_access") else "No"
        print(f"  - {role['name']}")
        print(f"    Custom: {custom}, Desk Access: {desk_access}, Disabled: {disabled}")
    
    return roles


def list_roles_by_category():
    """Listar roles categorizados"""
    roles = frappe.get_all(
        "Role",
        fields=["name", "desk_access", "is_custom"],
        order_by="name"
    )
    
    standard_roles = [r for r in roles if not r.get("is_custom")]
    custom_roles = [r for r in roles if r.get("is_custom")]
    
    print("\n=== Roles Estándar ===\n")
    for role in standard_roles[:20]:
        print(f"  - {role['name']}")
    
    print(f"\n=== Roles Personalizados ===\n")
    for role in custom_roles:
        print(f"  - {role['name']}")
    
    return standard_roles, custom_roles


def check_role_exists(role_name):
    """Verificar si un rol existe"""
    return frappe.db.exists("Role", role_name)


def get_role_permissions(role_name, doctype=None):
    """Obtener permisos de un rol para un DocType específico o todos"""
    filters = {"role": role_name}
    if doctype:
        filters["parent"] = doctype
    
    permissions = frappe.get_all(
        "DocPerm",
        filters=filters,
        fields=["parent", "role", "permlevel", "read", "write", "create", "delete", "submit", "cancel", "amend", "report", "export", "share", "print", "email", "import"]
    )
    
    return permissions


def list_critical_doctypes():
    """Listar DocTypes críticos para Barriofarma"""
    critical_doctypes = [
        "Receta Medica",
        "Sales Invoice",
        "Purchase Receipt",
        "Stock Entry",
        "Shelf",
        "Shelf Movement",
        "Item",
        "Customer",
        "Patient",
        "Doctor",
        "Payment Entry",
        "Purchase Invoice"
    ]
    
    print("\n=== DocTypes Críticos para Barriofarma ===\n")
    for dt in critical_doctypes:
        exists = frappe.db.exists("DocType", dt)
        status = "✓ Existe" if exists else "✗ No existe"
        print(f"  - {dt}: {status}")
    
    return critical_doctypes


def analyze_role_permissions_for_doctype(doctype):
    """Analizar permisos de todos los roles para un DocType"""
    permissions = frappe.get_all(
        "DocPerm",
        filters={"parent": doctype},
        fields=["role", "permlevel", "read", "write", "create", "delete", "submit", "cancel"],
        order_by="role"
    )
    
    print(f"\n=== Permisos para DocType: {doctype} ===\n")
    for perm in permissions:
        perms = []
        if perm.get("read"): perms.append("R")
        if perm.get("write"): perms.append("W")
        if perm.get("create"): perms.append("C")
        if perm.get("delete"): perms.append("D")
        if perm.get("submit"): perms.append("S")
        if perm.get("cancel"): perms.append("X")
        
        perm_level = f" (Level {perm.get('permlevel', 0)})" if perm.get("permlevel", 0) > 0 else ""
        print(f"  - {perm['role']}: {', '.join(perms) if perms else 'Sin permisos'}{perm_level}")
    
    return permissions


if __name__ == "__main__":
    frappe.init(site="barriofarma.localhost")
    frappe.connect()
    
    print("=" * 60)
    print("Análisis de Roles y Permisos - Story 8.1")
    print("=" * 60)
    
    # Listar todos los roles
    all_roles = list_all_roles()
    
    # Listar roles por categoría
    standard, custom = list_roles_by_category()
    
    # Verificar roles requeridos
    required_roles = [
        "Farmacéutico",
        "Auxiliar",
        "Bodeguero",
        "Administrativo",
        "Contabilidad",
        "Informática"
    ]
    
    print("\n=== Verificación de Roles Requeridos ===\n")
    for role_name in required_roles:
        exists = check_role_exists(role_name)
        status = "✓ Existe" if exists else "✗ No existe - CREAR"
        print(f"  - {role_name}: {status}")
    
    # Listar DocTypes críticos
    critical_doctypes = list_critical_doctypes()
    
    # Analizar permisos para DocTypes críticos
    print("\n=== Análisis de Permisos por DocType ===\n")
    for doctype in critical_doctypes[:3]:  # Solo primeros 3 para no saturar
        if frappe.db.exists("DocType", doctype):
            analyze_role_permissions_for_doctype(doctype)
    
    frappe.db.close()

