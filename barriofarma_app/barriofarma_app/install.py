# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Módulo de instalación y migración para Barriofarma App
Story 8.1: Refinamiento de Gestión de Usuarios y Roles
"""

import frappe


def after_migrate():
    """
    Hook ejecutado después de cada migración
    Configura roles y permisos personalizados
    """
    setup_custom_roles()
    setup_custom_permissions()


def setup_custom_roles():
    """
    Crear roles personalizados si no existen
    Sigue buenas prácticas de Frappe: idempotente y ejecutable en migraciones
    """
    from barriofarma_app.barriofarma_app.utils.setup_roles import create_custom_roles
    
    try:
        created = create_custom_roles()
        if created:
            frappe.logger().info(f"Story 8.1: Roles creados: {', '.join(created)}")
    except Exception as e:
        frappe.logger().error(f"Story 8.1: Error al crear roles: {str(e)}")


def setup_custom_permissions():
    """
    Configurar permisos personalizados para roles de Barriofarma
    Sigue buenas prácticas de Frappe: idempotente y ejecutable en migraciones
    """
    from barriofarma_app.barriofarma_app.utils.setup_permissions import setup_all_permissions
    
    try:
        setup_all_permissions()
        frappe.logger().info("Story 8.1: Permisos configurados correctamente")
    except Exception as e:
        frappe.logger().error(f"Story 8.1: Error al configurar permisos: {str(e)}")

