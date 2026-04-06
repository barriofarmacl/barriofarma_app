# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Script para verificar permisos de roles en UAT
Plan de UAT - Barriofarma

Uso:
    bench --site uat.barriofarma.cl execute \
        barriofarma_app.barriofarma_app.utils.verify_permissions.verify_all_roles
"""

import frappe
from frappe import _
import logging

logger = logging.getLogger(__name__)


# Roles a verificar
ROLES_TO_VERIFY = [
    "Farmacéutico",
    "Auxiliar",
    "Bodeguero",
    "Administrativo",
    "Contabilidad",
    "Informática"
]

# DocTypes principales a verificar
DOCTYPES_TO_VERIFY = [
    "Receta Medica",
    "Sales Invoice",
    "Purchase Receipt",
    "Stock Entry",
    "Item",
    "Customer",
    "Patient",
    "Doctor",
    "Shelf",
    "Shelf Movement"
]


def verify_role_permissions(role_name):
    """
    Verificar permisos de un rol específico
    
    Args:
        role_name: Nombre del rol
    
    Returns:
        Diccionario con resultados de verificación
    """
    if not frappe.db.exists("Role", role_name):
        logger.warning(f"Rol '{role_name}' no existe")
        return None
    
    logger.info(f"\nVerificando permisos para rol: {role_name}")
    logger.info("-" * 60)
    
    results = {
        "role": role_name,
        "doctypes": {}
    }
    
    for doctype in DOCTYPES_TO_VERIFY:
        if not frappe.db.exists("DocType", doctype):
            logger.debug(f"  {doctype}: No existe, omitiendo")
            continue
        
        # Obtener permisos del DocType para este rol
        doc = frappe.get_doc("DocType", doctype)
        
        role_perms = []
        for perm in doc.permissions:
            if perm.role == role_name and perm.permlevel == 0:
                role_perms = {
                    "read": perm.read,
                    "write": perm.write,
                    "create": perm.create,
                    "delete": perm.delete,
                    "submit": perm.submit if hasattr(perm, 'submit') else False,
                    "cancel": perm.cancel if hasattr(perm, 'cancel') else False,
                    "report": perm.report if hasattr(perm, 'report') else False,
                    "export": perm.export if hasattr(perm, 'export') else False,
                    "print": perm.print if hasattr(perm, 'print') else False
                }
                break
        
        results["doctypes"][doctype] = role_perms
        
        if role_perms:
            # Construir resumen de permisos
            perm_list = []
            if role_perms.get("read"):
                perm_list.append("Read")
            if role_perms.get("write"):
                perm_list.append("Write")
            if role_perms.get("create"):
                perm_list.append("Create")
            if role_perms.get("delete"):
                perm_list.append("Delete")
            if role_perms.get("submit"):
                perm_list.append("Submit")
            if role_perms.get("cancel"):
                perm_list.append("Cancel")
            if role_perms.get("report"):
                perm_list.append("Report")
            if role_perms.get("export"):
                perm_list.append("Export")
            if role_perms.get("print"):
                perm_list.append("Print")
            
            if perm_list:
                logger.info(f"  {doctype}: {', '.join(perm_list)}")
            else:
                logger.info(f"  {doctype}: Sin permisos (intencional)")
        else:
            logger.info(f"  {doctype}: Sin permisos configurados")
    
    return results


def verify_all_roles():
    """
    Verificar permisos de todos los roles definidos
    """
    logger.info("=" * 60)
    logger.info("VERIFICACIÓN DE PERMISOS POR ROL")
    logger.info("=" * 60)
    
    frappe.set_user("Administrator")
    
    all_results = {}
    
    for role_name in ROLES_TO_VERIFY:
        results = verify_role_permissions(role_name)
        if results:
            all_results[role_name] = results
    
    # Resumen
    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN DE VERIFICACIÓN")
    logger.info("=" * 60)
    
    for role_name, results in all_results.items():
        doctypes_with_perms = len([d for d, p in results["doctypes"].items() if p])
        doctypes_without_perms = len([d for d, p in results["doctypes"].items() if not p])
        
        logger.info(f"\n{role_name}:")
        logger.info(f"  DocTypes con permisos: {doctypes_with_perms}")
        logger.info(f"  DocTypes sin permisos: {doctypes_without_perms}")
    
    logger.info("=" * 60)
    
    return all_results


def verify_user_has_role(username, role_name):
    """
    Verificar si un usuario tiene un rol asignado
    
    Args:
        username: Nombre de usuario
        role_name: Nombre del rol
    
    Returns:
        True si el usuario tiene el rol, False en caso contrario
    """
    if not frappe.db.exists("User", username):
        logger.warning(f"Usuario '{username}' no existe")
        return False
    
    has_role = frappe.db.exists("Has Role", {
        "parent": username,
        "role": role_name
    })
    
    return bool(has_role)


def verify_user_permissions(username):
    """
    Verificar permisos de un usuario específico
    
    Args:
        username: Nombre de usuario
    
    Returns:
        Diccionario con roles y permisos del usuario
    """
    if not frappe.db.exists("User", username):
        logger.warning(f"Usuario '{username}' no existe")
        return None
    
    # Obtener roles del usuario
    roles = frappe.get_all("Has Role",
        filters={"parent": username},
        fields=["role"]
    )
    role_names = [r["role"] for r in roles]
    
    logger.info(f"\nVerificando permisos para usuario: {username}")
    logger.info(f"Roles asignados: {', '.join(role_names)}")
    logger.info("-" * 60)
    
    # Verificar permisos para cada rol
    user_perms = {}
    for role_name in role_names:
        results = verify_role_permissions(role_name)
        if results:
            user_perms[role_name] = results
    
    return {
        "username": username,
        "roles": role_names,
        "permissions": user_perms
    }


if __name__ == "__main__":
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "barriofarma.localhost"
    
    frappe.init(site=site)
    frappe.connect()
    
    verify_all_roles()
    
    frappe.db.close()
