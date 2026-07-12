# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Script para crear roles personalizados y configurar permisos básicos
Story 8.1: Refinamiento de Gestión de Usuarios y Roles

Buenas prácticas de Frappe:
- Idempotente: puede ejecutarse múltiples veces sin efectos secundarios
- Ejecutable en migraciones: se ejecuta automáticamente en after_migrate hook
- Usa logging en lugar de print para producción
"""

import frappe
from frappe import _
import logging

logger = logging.getLogger(__name__)


def create_custom_roles():
    """
    Crear roles personalizados para Barriofarma si no existen
    """
    roles_to_create = [
        {
            "name": "Auxiliar",
            "desk_access": 1,
            "description": "Rol para auxiliares de farmacia. Acceso a ventas, búsqueda de productos y registro de clientes."
        },
        {
            "name": "Bodeguero",
            "desk_access": 1,
            "description": "Rol para bodegueros. Acceso a inventario, recepciones y movimientos de stock."
        },
        {
            "name": "Administrativo",
            "desk_access": 1,
            "description": "Rol para personal administrativo. Acceso a reportes y configuración básica."
        },
        {
            "name": "Contabilidad",
            "desk_access": 1,
            "description": "Rol para personal de contabilidad. Acceso a facturas, pagos y reportes financieros."
        },
        {
            "name": "Informática",
            "desk_access": 1,
            "description": "Rol para personal de informática. Acceso técnico completo y configuración avanzada."
        },
        {
            "name": "Vendedor Terreno",
            "desk_access": 0,
            "description": "Rol para vendedores en terreno. Acceso solo via SPA inicio/API REST (catalogo, carrito, Sales Order propias)."
        }
    ]
    
    created_roles = []
    
    for role_data in roles_to_create:
        role_name = role_data["name"]
        
        if frappe.db.exists("Role", role_name):
            logger.debug(f"Rol '{role_name}' ya existe, omitiendo creación")
            continue
        
        try:
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": role_data.get("desk_access", 1),
                "is_custom": 1  # Marcar como rol personalizado
            })
            
            if "description" in role_data:
                role.description = role_data["description"]
            
            role.insert(ignore_permissions=True)
            frappe.db.commit()
            created_roles.append(role_name)
            logger.info(f"Rol '{role_name}' creado exitosamente")
            
        except Exception as e:
            logger.error(f"Error al crear rol '{role_name}': {str(e)}")
            frappe.db.rollback()
    
    return created_roles


def setup_basic_permissions():
    """
    Configurar permisos básicos para roles personalizados
    Nota: Permisos detallados se configuran automáticamente en setup_permissions.py
    """
    logger.debug("Permisos básicos: Todos los roles tienen acceso al desk (desk_access=1)")
    logger.debug("Permisos específicos por DocType se configuran en setup_permissions.py")


def verify_roles():
    """Verificar que todos los roles requeridos existen"""
    required_roles = [
        "Farmacéutico",
        "Auxiliar",
        "Bodeguero",
        "Administrativo",
        "Contabilidad",
        "Informática",
        "Vendedor Terreno"
    ]
    
    logger.info("=== Verificación de Roles Requeridos ===")
    all_exist = True
    
    for role_name in required_roles:
        exists = frappe.db.exists("Role", role_name)
        status = "Existe" if exists else "No existe"
        logger.info(f"  {role_name:20} {status}")
        if not exists:
            all_exist = False
    
    return all_exist


if __name__ == "__main__":
    # Para ejecución manual desde consola
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "barriofarma.localhost"
    
    frappe.init(site=site)
    frappe.connect()
    
    logger.info("=" * 60)
    logger.info("Setup de Roles Personalizados - Story 8.1")
    logger.info("=" * 60)
    
    # Verificar roles existentes
    logger.info("=== Verificación Inicial ===")
    verify_roles()
    
    # Crear roles faltantes
    logger.info("=== Creación de Roles ===")
    created = create_custom_roles()
    
    if created:
        logger.info(f"{len(created)} roles creados: {', '.join(created)}")
    else:
        logger.info("Todos los roles ya existen")
    
    # Configurar permisos básicos
    setup_basic_permissions()
    
    # Verificación final
    logger.info("=== Verificación Final ===")
    all_exist = verify_roles()
    
    if all_exist:
        logger.info("Todos los roles requeridos están disponibles")
    else:
        logger.warning("Algunos roles aún no existen")
    
    frappe.db.close()
    logger.info("=" * 60)

