# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Script para configurar permisos por DocType para roles personalizados
Story 8.1: Refinamiento de Gestión de Usuarios y Roles

ESTRATEGIA DE PERMISOS (3 niveles de prioridad):
1. Específico (PERMISSIONS_MATRIX): Permisos definidos explícitamente por DocType
2. Base del Módulo (MODULE_BASE_PERMISSIONS): Permisos por defecto del módulo ERPNext
3. Sin permisos: No se configura nada (mantiene permisos estándar de ERPNext)

VENTAJAS:
- Control centralizado y automatizado de permisos
- Escalable: fácil agregar nuevos roles o DocTypes
- Mantenible: matriz de permisos es auto-documentación
- Versionable: cambios en Git, fácil rollback
- Idempotente: puede ejecutarse múltiples veces sin efectos secundarios

Buenas prácticas de Frappe:
- Idempotente: puede ejecutarse múltiples veces sin efectos secundarios
- Ejecutable en migraciones: se ejecuta automáticamente en after_migrate hook
- No modifica DocTypes estándar de forma permanente: los cambios se aplican pero no se exportan
- Usa logging en lugar de print para producción
"""

import frappe
from frappe import _
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# PERMISOS BASE POR MÓDULO Y ROL
# ============================================================================
# Define permisos por defecto para cada módulo de ERPNext
# Si un DocType no está en PERMISSIONS_MATRIX, se aplican estos permisos base
# Formato: {module_name: {role: [permisos]}}
# Permisos: R=Read, W=Write, C=Create, D=Delete, S=Submit, X=Cancel

MODULE_BASE_PERMISSIONS = {
    # Módulo: Stock (Inventario)
    "Stock": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C", "S"],  # Control total
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Accounts (Contabilidad)
    "Accounts": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "C", "S"],  # Control total
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Selling (Ventas)
    "Selling": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R"],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "S", "X"],  # Puede cancelar facturas
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Buying (Compras)
    "Buying": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C", "S"],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "S", "X"],  # Puede procesar facturas
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Manufacturing (Manufactura) - No aplica para farmacia
    "Manufacturing": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": [],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: Projects (Proyectos) - No aplica para farmacia
    "Projects": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": [],
        "Administrativo": [],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    # Módulo: CRM
    "CRM": {
        "Farmacéutico": [],
        "Auxiliar": [],
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
# Prioridad máxima: si un DocType está aquí, se usan estos permisos
# Formato: {doctype: {role: [permisos]}}
# Permisos: R=Read, W=Write, C=Create, D=Delete, S=Submit, X=Cancel

PERMISSIONS_MATRIX = {
    "Receta Medica": {
        "Farmacéutico": ["R", "W", "C", "S"],
        "Auxiliar": ["R"],
        "Bodeguero": [],
        "Administrativo": [],
        "Contabilidad": [],
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
    "Purchase Receipt": {
        "Farmacéutico": ["R", "W", "S"],
        "Auxiliar": ["R", "W", "C"],
        "Bodeguero": ["R"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Purchase Order": {
        "Farmacéutico": ["R", "W", "C", "S"],
        "Auxiliar": ["R"],
        "Bodeguero": ["R", "W", "C", "S"],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
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
    "Item": {
        "Farmacéutico": ["R", "W", "C"],  # Maestro de producto / medicamento
        "Auxiliar": ["R", "W"],  # Editar existentes (imagen, datos operativos); no crear ítems
        "Bodeguero": ["R", "W", "C"],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
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
    "POS Invoice": {
        "Farmacéutico": ["R", "W", "C", "S"],  # Puede crear ventas POS
        "Auxiliar": ["R", "W", "C", "S"],  # Puede crear ventas POS
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "POS Profile": {
        "Farmacéutico": ["R"],  # Necesita leer POS Profile para crear POS Invoice
        "Auxiliar": ["R"],  # Necesita leer POS Profile para crear POS Invoice
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Price List": {
        "Farmacéutico": ["R", "W", "C"],
        "Auxiliar": ["R"],
        "Bodeguero": ["R"],
        "Administrativo": ["R", "W", "C"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Item Price": {
        "Farmacéutico": ["R", "W", "C"],
        "Auxiliar": ["R"],
        "Bodeguero": ["R"],
        "Administrativo": ["R", "W", "C"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "POS Opening Entry": {
        "Farmacéutico": ["R", "W", "C", "S"],  # Necesita crear y validar POS Opening Entry para usar el POS
        "Auxiliar": ["R", "W", "C", "S"],  # Necesita crear y validar POS Opening Entry para usar el POS
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "POS Closing Entry": {
        "Farmacéutico": ["R", "W", "C", "S"],  # Cierre de caja POS
        "Auxiliar": ["R", "W", "C", "S"],  # Cierre de caja POS (función principal en mostrador)
        "Bodeguero": [],
        "Administrativo": ["R"],
        "Contabilidad": ["R", "W", "C", "S"],
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
    "Supplier": {
        "Farmacéutico": ["R"],
        "Auxiliar": ["R"],
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
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Batch": {
        "Farmacéutico": ["R"],
        "Auxiliar": ["R"],
        "Bodeguero": ["R", "W", "C"],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Material Request": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C", "S"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Request for Quotation": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C", "S"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Supplier Quotation": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R", "W", "C", "S"],
        "Administrativo": ["R"],
        "Contabilidad": [],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Quotation": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R"],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Sales Order": {
        "Farmacéutico": [],
        "Auxiliar": [],
        "Bodeguero": ["R"],
        "Administrativo": ["R"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Company": {
        "Farmacéutico": ["R"],
        "Auxiliar": ["R"],
        "Bodeguero": ["R"],
        "Administrativo": ["R", "W", "C"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
    "Letter Head": {
        "Farmacéutico": ["R"],
        "Auxiliar": ["R"],
        "Bodeguero": [],
        "Administrativo": ["R", "W", "C"],
        "Contabilidad": ["R"],
        "Informática": ["R", "W", "C", "D", "S", "X"]
    },
}


# ============================================================================
# DOCTYPES EXCLUIDOS (NO CONFIGURAR PERMISOS)
# ============================================================================
# DocTypes que NO deben tener permisos configurados automáticamente
# (por ejemplo, DocTypes del sistema, configuraciones, etc.)

# Roles operativos UAT: solo DocTypes en PERMISSIONS_MATRIX (o base módulo explícito).
# Evita que la estrategia extendida herede permisos genéricos de ERPNext por módulo.
OPERATIONAL_WHITELIST_ROLES = frozenset({"Farmacéutico", "Auxiliar"})

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


# ============================================================================
# FUNCIONES HELPER PARA ESTRATEGIA EXTENDIDA
# ============================================================================

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
        module_name: Nombre del módulo (ej: "Stock", "Accounts")
        role: Nombre del rol
    
    Returns:
        Lista de permisos o [] si no hay permisos base
    """
    if module_name in MODULE_BASE_PERMISSIONS:
        return MODULE_BASE_PERMISSIONS[module_name].get(role, [])
    
    return []


def get_doctype_permissions(doctype, role):
    """
    Obtener permisos para un DocType y rol específico
    Prioridad: Específico (PERMISSIONS_MATRIX) > Base del módulo > []
    
    Args:
        doctype: Nombre del DocType
        role: Nombre del rol
    
    Returns:
        Lista de permisos o None si no se deben configurar permisos
    """
    # 1. Permisos específicos (máxima prioridad)
    if doctype in PERMISSIONS_MATRIX and role in PERMISSIONS_MATRIX[doctype]:
        return PERMISSIONS_MATRIX[doctype][role]

    # 2. Permisos base del módulo (incluye [] explícito = sin acceso)
    module_name = get_doctype_module(doctype)
    if module_name and module_name in MODULE_BASE_PERMISSIONS:
        if role in MODULE_BASE_PERMISSIONS[module_name]:
            return MODULE_BASE_PERMISSIONS[module_name][role]

    # 3. Roles operativos: denegar por defecto (no heredar ERPNext estándar)
    if role in OPERATIONAL_WHITELIST_ROLES:
        return []

    # 4. Otros roles: no tocar DocPerm estándar
    return None


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def _build_perm_values(permissions, is_submittable):
    """Construir dict de flags DocPerm desde lista R/W/C/D/S/X."""
    return {
        "read": "R" in permissions,
        "write": "W" in permissions,
        "create": "C" in permissions,
        "delete": "D" in permissions,
        "submit": "S" in permissions and is_submittable and "W" in permissions,
        "cancel": "X" in permissions and is_submittable and "W" in permissions,
        "amend": False,
        "report": "R" in permissions,
        "export": "R" in permissions,
        "share": False,
        "print": "R" in permissions,
        "email": False,
        "import": False,
    }


def _sync_custom_docperm(doctype, role, perm_values, permlevel=0):
    """
    Sincronizar Custom DocPerm cuando el DocType ya usa permisos custom.

    En Frappe v16, si existen filas en Custom DocPerm para un DocType, esas filas
    sustituyen a DocPerm estándar para permisos efectivos.
    """
    filters = {"parent": doctype, "role": role, "permlevel": permlevel}
    custom_name = frappe.db.get_value("Custom DocPerm", filters)

    if custom_name:
        custom = frappe.get_doc("Custom DocPerm", custom_name)
        for key, value in perm_values.items():
            if hasattr(custom, "meta") and custom.meta.has_field(key):
                setattr(custom, key, value)
            elif hasattr(custom, key):
                setattr(custom, key, value)
        custom.save(ignore_permissions=True)
        return True

    if frappe.db.exists("Custom DocPerm", {"parent": doctype}):
        if not any(perm_values.get(k) for k in ("read", "write", "create", "delete", "submit")):
            return False
        frappe.get_doc(
            {
                "doctype": "Custom DocPerm",
                "parent": doctype,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "permlevel": permlevel,
                **perm_values,
            }
        ).insert(ignore_permissions=True)
        return True

    return False


def remove_docperm(doctype, role, permlevel=0):
	"""
	Elimina permisos del rol en el DocType.

	Frappe no permite guardar DocPerm con todos los flags en 0; para denegar
	acceso hay que quitar la fila (permiso efectivo = sin acceso vía ese rol).
	"""
	if not frappe.db.exists("DocType", doctype) or not frappe.db.exists("Role", role):
		return False

	try:
		doc = frappe.get_doc("DocType", doctype)
		before = len(doc.permissions)
		doc.permissions = [
			p
			for p in doc.permissions
			if not (p.role == role and p.permlevel == permlevel)
		]
		if len(doc.permissions) < before:
			doc.save(ignore_permissions=True)

		custom_name = frappe.db.get_value(
			"Custom DocPerm", {"parent": doctype, "role": role, "permlevel": permlevel}
		)
		if custom_name:
			frappe.delete_doc("Custom DocPerm", custom_name, ignore_permissions=True)

		frappe.db.commit()
		return True
	except Exception as e:
		logger.error(f"Error al quitar permiso {doctype}/{role}: {e}")
		frappe.db.rollback()
		return False


def set_docperm(doctype, role, permissions, permlevel=0):
    """
    Configurar permisos para un DocType y rol específico
    
    Args:
        doctype: Nombre del DocType
        role: Nombre del rol
        permissions: Lista de permisos ['R', 'W', 'C', 'D', 'S', 'X']
        permlevel: Nivel de permiso (0 = nivel base)
    """
    if not frappe.db.exists("DocType", doctype):
        logger.warning(f"DocType '{doctype}' no existe, omitiendo configuración de permisos")
        return False
    
    if not frappe.db.exists("Role", role):
        logger.warning(f"Rol '{role}' no existe, omitiendo configuración de permisos")
        return False

    if not permissions:
        return remove_docperm(doctype, role, permlevel)
    
    try:
        # Obtener el DocType
        doc = frappe.get_doc("DocType", doctype)
        
        # Buscar permiso existente para este rol y nivel
        existing_perm = None
        for perm in doc.permissions:
            if perm.role == role and perm.permlevel == permlevel:
                existing_perm = perm
                break
        
        # Verificar si el DocType es submittable
        is_submittable = doc.is_submittable
        perm_values = _build_perm_values(permissions, is_submittable)
        _sync_custom_docperm(doctype, role, perm_values, permlevel)
        
        if existing_perm:
            # Actualizar permiso existente
            for key, value in perm_values.items():
                setattr(existing_perm, key, value)
        else:
            # Crear nuevo permiso
            doc.append("permissions", {
                "role": role,
                "permlevel": permlevel,
                **perm_values
            })
        
        # Guardar el DocType
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error al configurar permiso para {doctype}/{role}: {str(e)}")
        frappe.db.rollback()
        return False


def setup_permissions_for_role(role_name, use_extended_strategy=True):
    """
    Configurar permisos para un rol específico
    
    Args:
        role_name: Nombre del rol
        use_extended_strategy: Si True, usa estrategia extendida (específico > módulo > sin permisos)
                              Si False, solo usa PERMISSIONS_MATRIX (compatibilidad hacia atrás)
    """
    logger.info(f"Configurando permisos para rol: {role_name}")
    
    configured = 0
    skipped = 0
    
    if use_extended_strategy:
        # ESTRATEGIA EXTENDIDA: Configurar todos los DocTypes relevantes
        # Obtener todos los DocTypes del sistema
        all_doctypes = frappe.get_all("DocType", 
            filters={"custom": 0},  # DocTypes estándar
            fields=["name"]
        )
        
        # Agregar DocTypes personalizados
        custom_doctypes = frappe.get_all("DocType",
            filters={"custom": 1},
            fields=["name"]
        )
        all_doctypes.extend(custom_doctypes)
        
        for doctype_info in all_doctypes:
            doctype = doctype_info["name"]
            
            # Excluir DocTypes del sistema
            if doctype in EXCLUDED_DOCTYPES:
                continue
            
            # Obtener permisos usando estrategia de 3 niveles
            permissions = get_doctype_permissions(doctype, role_name)
            
            if permissions is not None:
                if permissions:
                    if set_docperm(doctype, role_name, permissions):
                        configured += 1
                        logger.debug(f"  {doctype}: {', '.join(permissions)}")
                    else:
                        skipped += 1
                elif remove_docperm(doctype, role_name):
                    configured += 1
                    logger.debug(f"  {doctype}: permiso eliminado (sin acceso)")
                else:
                    skipped += 1
            # Si permissions es None, no se configura (mantiene permisos estándar)
    else:
        # ESTRATEGIA ORIGINAL: Solo PERMISSIONS_MATRIX (compatibilidad hacia atrás)
        for doctype, roles_perms in PERMISSIONS_MATRIX.items():
            if role_name in roles_perms:
                permissions = roles_perms[role_name]
                if permissions:
                    if set_docperm(doctype, role_name, permissions):
                        configured += 1
                        perms_str = ", ".join(permissions)
                        logger.debug(f"  {doctype}: {perms_str}")
                    else:
                        skipped += 1
                else:
                    logger.debug(f"  {doctype}: Sin permisos (intencional)")
                    skipped += 1
    
    return configured, skipped


def setup_all_permissions(use_extended_strategy=True):
    """
    Configurar permisos para todos los roles personalizados
    
    Args:
        use_extended_strategy: Si True, usa estrategia extendida (todos los DocTypes)
                              Si False, solo usa PERMISSIONS_MATRIX (compatibilidad)
    """
    roles = [
        "Farmacéutico",
        "Auxiliar",
        "Bodeguero",
        "Administrativo",
        "Contabilidad",
        "Informática"
    ]
    
    if use_extended_strategy:
        logger.info("=== Configuración Extendida de Permisos ===")
        logger.info("Estrategia: Específico > Base del módulo > Sin permisos")
    else:
        logger.info("=== Configuración de Permisos por Rol ===")
        logger.info("Estrategia: Solo PERMISSIONS_MATRIX (compatibilidad)")
    
    total_configured = 0
    total_skipped = 0
    
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            logger.warning(f"Rol '{role_name}' no existe, omitiendo")
            continue
        
        configured, skipped = setup_permissions_for_role(role_name, use_extended_strategy)
        total_configured += configured
        total_skipped += skipped
    
    logger.info(f"Resumen: {total_configured} permisos configurados, {total_skipped} omitidos")
    
    frappe.db.commit()


if __name__ == "__main__":
    # Para ejecución manual desde consola
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "frontend"
    
    frappe.init(site=site)
    frappe.connect()
    
    logger.info("=" * 60)
    logger.info("Setup de Permisos por DocType - Story 8.1")
    logger.info("Estrategia Extendida: Específico > Módulo > Sin permisos")
    logger.info("=" * 60)
    
    # Usar estrategia extendida por defecto
    setup_all_permissions(use_extended_strategy=True)
    
    logger.info("=" * 60)
    logger.info("✓ Configuración de permisos completada")
    logger.info("=" * 60)
    
    frappe.db.close()

