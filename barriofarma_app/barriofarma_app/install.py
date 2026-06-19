# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Módulo de instalación y migración para Barriofarma App
Story 8.1: Refinamiento de Gestión de Usuarios y Roles
"""

import frappe


def after_install():
    """Hook tras instalar la app en un sitio nuevo (QA/UAT/PROD/dev).

    Asegura el locale del entorno desde el minuto cero para que un fresh install
    no quede en el default Asia/Kolkata de Frappe.
    """
    setup_site_locale()


def after_migrate():
    """
    Hook ejecutado después de cada migración
    Configura roles y permisos personalizados
    """
    setup_custom_roles()
    setup_custom_permissions()
    setup_pos_page_access()
    setup_stock_page_access()
    sync_stock_entry_shelf_ui_fields()
    setup_selling_dashboard_access()
    setup_buying_dashboard_access()
    setup_stock_dashboard_access()
    setup_admin_accounting_access()
    setup_barriofarma_dashboard_widgets()
    setup_informatica_maintainer()
    setup_site_locale()


def setup_site_locale():
    """Zona horaria America/Santiago (evita fechas POS/reportes desfasadas)."""
    from barriofarma_app.barriofarma_app.utils.setup.setup_site_locale import (
        ensure_barriofarma_site_locale,
    )

    try:
        changed = ensure_barriofarma_site_locale()
        if changed:
            frappe.logger().info("BarrioFarma site locale: %s", "; ".join(changed))
    except Exception as e:
        frappe.logger().error("BarrioFarma site locale: %s", str(e))


def setup_barriofarma_dashboard_widgets():
    """Number Card / Dashboard Chart BF + embed Selling/Buying/Stock."""
    from barriofarma_app.barriofarma_app.utils.dashboard.barriofarma_dashboard_widgets import (
        setup_barriofarma_dashboard,
    )

    try:
        setup_barriofarma_dashboard()
    except Exception as e:
        frappe.logger().error("BarrioFarma dashboard widgets: %s", str(e))


def setup_informatica_maintainer():
    """Rol mantenedor prod: eduardo.araya@barriofarma.cl."""
    from barriofarma_app.barriofarma_app.utils.setup.setup_informatica_maintainer import (
        ensure_informatica_maintainer_roles,
    )

    try:
        added = ensure_informatica_maintainer_roles()
        if added:
            frappe.logger().info("Informática maintainer roles: %s", ", ".join(added))
    except Exception as e:
        frappe.logger().error("Informática maintainer setup: %s", str(e))


def setup_custom_roles():
    """
    Crear roles personalizados si no existen
    Sigue buenas prácticas de Frappe: idempotente y ejecutable en migraciones
    """
    from barriofarma_app.barriofarma_app.utils.permissions.setup_roles import create_custom_roles
    
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
    from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import setup_all_permissions
    
    try:
        setup_all_permissions()
        frappe.logger().info("Story 8.1: Permisos configurados correctamente")
    except Exception as e:
        frappe.logger().error(f"Story 8.1: Error al configurar permisos: {str(e)}")


def setup_pos_page_access():
    """Permite POS Desk a roles Farmacéutico y Auxiliar (sin Sales User)."""
    from barriofarma_app.barriofarma_app.utils.permissions.setup_pos_page_access import (
        setup_point_of_sale_page_roles,
    )

    try:
        added = setup_point_of_sale_page_roles()
        if added:
            frappe.logger().info(
                "Story 8.1: roles POS page añadidos: %s", ", ".join(added)
            )
    except Exception as e:
        frappe.logger().error("Story 8.1: Error setup POS page: %s", str(e))


def setup_stock_page_access():
    """Page stock-balance (Resumen de existencia) para Auxiliar/Farmacéutico."""
    from barriofarma_app.barriofarma_app.utils.permissions.setup_stock_page_access import (
        setup_stock_balance_page_roles,
    )

    try:
        added = setup_stock_balance_page_roles()
        if added:
            frappe.logger().info("Story 8.1: Page stock-balance roles: %s", ", ".join(added))
    except Exception as e:
        frappe.logger().error("Story 8.1: Error Page stock-balance: %s", str(e))


def sync_stock_entry_shelf_ui_fields():
    """Columnas Estante origen/destino visibles en grilla Stock Entry."""
    from barriofarma_app.barriofarma_app.utils.permissions.sync_stock_entry_shelf_fields import (
        sync_stock_entry_shelf_grid_fields,
    )

    try:
        sync_stock_entry_shelf_grid_fields()
    except Exception as e:
        frappe.logger().error("Story 8.1: sync Stock Entry shelf fields: %s", str(e))


def setup_selling_dashboard_access():
    """Reportes del tablero Ventas para perfiles operativos."""
    from barriofarma_app.barriofarma_app.utils.permissions.setup_selling_dashboard_access import (
        setup_selling_dashboard_reports,
    )

    try:
        added = setup_selling_dashboard_reports()
        if added:
            frappe.logger().info("Story 8.1: reportes tablero Ventas: %s", "; ".join(added))
    except Exception as e:
        frappe.logger().error("Story 8.1: Error tablero Ventas: %s", str(e))


def setup_buying_dashboard_access():
    """Gráficos del tablero Compras para Farmacéutico e Informática (no Auxiliar)."""
    from barriofarma_app.barriofarma_app.utils.permissions.setup_buying_dashboard_access import (
        setup_buying_dashboard_reports,
    )

    try:
        added = setup_buying_dashboard_reports()
        if added:
            frappe.logger().info("Story 8.1: reportes tablero Compras: %s", "; ".join(added))
    except Exception as e:
        frappe.logger().error("Story 8.1: Error tablero Compras: %s", str(e))


def setup_stock_dashboard_access():
    """Reportes de existencias y tablero Stock para perfiles operativos."""
    from barriofarma_app.barriofarma_app.utils.permissions.setup_stock_dashboard_access import (
        apply_stock_dashboard_access,
    )

    try:
        added = apply_stock_dashboard_access()
        if added:
            frappe.logger().info("Story 8.1: reportes Stock: %s", "; ".join(added))
    except Exception as e:
        frappe.logger().error("Story 8.1: Error reportes Stock: %s", str(e))


def setup_admin_accounting_access():
    """Perfiles administrativos: roles ERPNext estándar (sin DocPerm custom restrictivo)."""
    from barriofarma_app.barriofarma_app.utils.permissions.setup_admin_accounting_access import (
        apply_admin_profiles,
    )

    try:
        results = apply_admin_profiles()
        ok = [r["email"] for r in results if r.get("success")]
        if ok:
            frappe.logger().info("Story 8.1: perfiles administrativos: %s", ", ".join(ok))
    except Exception as e:
        frappe.logger().error("Story 8.1: Error perfiles admin: %s", str(e))


def before_tests():
    """ERPNext 16 bootstrap + estantes BarrioFarma (Issue #58, erpnext-v16-platform-upgrade)."""
    from barriofarma_app.barriofarma_app.utils.setup.erpnext_test_bootstrap import before_tests as _bootstrap

    _bootstrap()

