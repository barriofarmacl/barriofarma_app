# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Estrategia extendida para configurar permisos en módulos estándar de ERPNext
y DocTypes personalizados de forma automatizada y centralizada.

VENTAJAS:
1. Control centralizado de permisos para toda la aplicación
2. Fácil de mantener y auditar
3. Idempotente: puede ejecutarse múltiples veces
4. Escalable: fácil agregar nuevos roles o DocTypes
5. Versionable: cambios en Git, fácil rollback
6. Documentado: la matriz es auto-documentación

ESTRATEGIA:
- Separar permisos por módulo de negocio
- Definir permisos base por rol
- Permitir sobrescritura específica por DocType
- Respetar permisos estándar de ERPNext cuando no se especifican
"""

import frappe
from frappe import _
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# PERMISOS BASE POR MÓDULO Y ROL
# ============================================================================
# Define permisos por defecto para cada módulo de ERPNext
# Si un DocType no está en la matriz específica, se aplican estos permisos base

MODULE_BASE_PERMISSIONS = {
    # Módulo: Stock (Inventario)
    "stock": {
        "Farmacéutico": ["R"],  # Solo lectura por defecto
        "Auxiliar": ["R"],
        "Bodeguero": ["R", "W", "C", "S"],  # Control total
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Accounts (Contabilidad)
    "accounts": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "C", "S"],  # Control total
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Selling (Ventas)
    "selling": {
        "Farmacéutico": ["R", "W", "C", "S"],  # Puede vender
        "Auxiliar": ["R", "W", "C", "S"],  # Puede vender
        "Bodeguero": ["R"],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "S", "X"],  # Puede cancelar facturas
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Buying (Compras)
    "buying": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C", "S"],  # Control total
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "S", "X"],  # Puede procesar facturas
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Manufacturing (Manufactura) - No aplica para farmacia
    "manufacturing": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": [],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Projects (Proyectos) - No aplica para farmacia
    "projects": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": [],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: CRM
    "crm": {
        "Farmacéutico": ["R", "W", "C"],
        "Auxiliar": ["R", "W", "C"],
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    }
}


# ============================================================================
# PERMISOS ESPECÍFICOS POR DOCTYPE (SOBRESCRITURA)
# ============================================================================
# Permisos específicos que sobrescriben los permisos base del módulo
# Útil para casos especiales o DocTypes personalizados

SPECIFIC_DOCTYPE_PERMISSIONS = {
    # DocTypes personalizados de Barriofarma
    "Receta Medica": {
        "Farmacéutico": ["R", "W", "C", "S"],
        "Auxiliar": ["R"],
        "Bodeguero": [],
        "Administrativo": [],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Shelf": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Shelf Movement": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Patient": {
        "Farmacéutico": ["R", "W", "C"],
        "Auxiliar": ["R", "W", "C"],
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Doctor": {
        "Farmacéutico": ["R", "W", "C"],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": [],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    
    # DocTypes estándar de ERPNext con permisos específicos
    "Item": {
        "Farmacéutico": ["R", "W", "C"],  # Puede crear items
        "Auxiliar": ["R"],
        "Bodeguero": ["R", "W", "C"],  # Puede crear items
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Sales Invoice": {
        "Farmacéutico": ["R", "W", "C", "S"],  # Solo con receta
        "Auxiliar": ["R", "W", "C", "S"],  # Solo venta libre
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "S", "X"],  # Necesita Write para Submit/Cancel
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "POS Invoice": {
        "Farmacéutico": ["R", "W", "C", "S"],  # Puede crear ventas POS
        "Auxiliar": ["R", "W", "C", "S"],  # Puede crear ventas POS
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Purchase Receipt": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C", "S"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Stock Entry": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C", "S"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Payment Entry": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "C", "S"],  # Puede crear y procesar pagos
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Journal Entry": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "C", "S"],  # Puede crear y contabilizar
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Purchase Invoice": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "S", "X"],  # Necesita Write para Submit/Cancel
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Customer": {
        "Farmacéutico": ["R", "W", "C"],
        "Auxiliar": ["R", "W", "C"],
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Supplier": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C"],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Warehouse": {
        "Farmacéutico": ["R"],
        "Auxiliar": ["R"],
        "Bodeguero": ["R", "W", "C"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Batch": {
        # Farm/Aux: create/write maestro de lote (whiteboard #78 PR1)
        "Farmacéutico": ["R", "W", "C"],
        "Auxiliar": ["R", "W", "C"],
        "Bodeguero": ["R", "W", "C"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Serial No": {
        # Alineado a Batch para trazabilidad serie en Desk (whiteboard #78 PR1)
        "Farmacéutico": ["R", "W", "C"],
        "Auxiliar": ["R", "W", "C"],
        "Bodeguero": ["R", "W", "C"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    }
}


# ============================================================================
# DOCTYPES EXCLUIDOS (NO CONFIGURAR PERMISOS)
# ============================================================================
# DocTypes que NO deben tener permisos configurados automáticamente
# (por ejemplo, DocTypes del sistema, configuraciones, etc.)

EXCLUDED_DOCTYPES = [
    "Role",
    "User",
    "User Permission",
    "Custom Field",
    "Custom DocPerm",
    "Customize Form",
    "Property Setter",
    "Workflow",
    "Workflow State",
    "Workflow Action",
    "Print Format",
    "Letter Head",
    "Email Account",
    "Email Queue",
    "Communication",
    "File",
    "Version",
    "Error Log",
    "Scheduled Job Type",
    "Scheduled Job Log"
]


def get_doctype_module(doctype):
    """
    Obtener el módulo al que pertenece un DocType
    
    Args:
        doctype: Nombre del DocType
    
    Returns:
        Nombre del módulo o None si no se encuentra
    """
    try:
        doc = frappe.get_doc("DocType", doctype)
        return doc.module
    except:
        return None


def get_module_base_permissions(module_name, role):
    """
    Obtener permisos base para un módulo y rol
    
    Args:
        module_name: Nombre del módulo (ej: "stock", "accounts")
        role: Nombre del rol
    
    Returns:
        Lista de permisos o [] si no hay permisos base
    """
    # Normalizar nombre del módulo
    module_key = module_name.lower().replace(" ", "_")
    
    # Buscar en permisos base
    if module_key in MODULE_BASE_PERMISSIONS:
        return MODULE_BASE_PERMISSIONS[module_key].get(role, [])
    
    return []


def get_doctype_permissions(doctype, role):
    """
    Obtener permisos para un DocType y rol específico
    Prioridad: Específico > Base del módulo > []
    
    Args:
        doctype: Nombre del DocType
        role: Nombre del rol
    
    Returns:
        Lista de permisos
    """
    # 1. Verificar permisos específicos (máxima prioridad)
    if doctype in SPECIFIC_DOCTYPE_PERMISSIONS:
        return SPECIFIC_DOCTYPE_PERMISSIONS[doctype].get(role, [])
    
    # 2. Verificar permisos base del módulo
    module_name = get_doctype_module(doctype)
    if module_name:
        module_perms = get_module_base_permissions(module_name, role)
        if module_perms:
            return module_perms
    
    # 3. Sin permisos (no configurar)
    return []


def setup_permissions_for_all_doctypes():
    """
    Configurar permisos para todos los DocTypes relevantes
    Usa la estrategia de permisos específicos > permisos base del módulo
    """
    from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import set_docperm
    
    logger.info("=== Configuración Extendida de Permisos ===")
    logger.info("Estrategia: Específico > Base del módulo > Sin permisos")
    
    # Obtener todos los DocTypes del sistema
    all_doctypes = frappe.get_all("DocType", 
        filters={"custom": 0},  # Solo DocTypes estándar
        fields=["name", "module"]
    )
    
    # Agregar DocTypes personalizados
    custom_doctypes = frappe.get_all("DocType",
        filters={"custom": 1},
        fields=["name", "module"]
    )
    all_doctypes.extend(custom_doctypes)
    
    configured = 0
    skipped = 0
    excluded = 0
    
    roles = ["Farmacéutico", "Auxiliar", "Bodeguero", "Administrativo", "Contabilidad", "Informática"]
    
    for doctype_info in all_doctypes:
        doctype = doctype_info["name"]
        
        # Excluir DocTypes del sistema
        if doctype in EXCLUDED_DOCTYPES:
            excluded += 1
            continue
        
        # Configurar permisos para cada rol
        for role in roles:
            permissions = get_doctype_permissions(doctype, role)
            
            if permissions:
                if set_docperm(doctype, role, permissions):
                    configured += 1
                    logger.debug(f"  {doctype}/{role}: {', '.join(permissions)}")
                else:
                    skipped += 1
            else:
                # Sin permisos configurados (intencional)
                skipped += 1
    
    logger.info(f"\nResumen:")
    logger.info(f"  Permisos configurados: {configured}")
    logger.info(f"  Omitidos: {skipped}")
    logger.info(f"  Excluidos: {excluded}")
    
    frappe.db.commit()


if __name__ == "__main__":
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "barriofarma.localhost"
    
    frappe.init(site=site)
    frappe.connect()
    
    logger.info("=" * 60)
    logger.info("Setup Extendido de Permisos - Todos los DocTypes")
    logger.info("=" * 60)
    
    setup_permissions_for_all_doctypes()
    
    logger.info("=" * 60)
    logger.info("✓ Configuración extendida de permisos completada")
    logger.info("=" * 60)
    
    frappe.db.close()
