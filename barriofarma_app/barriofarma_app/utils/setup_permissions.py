# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Script para configurar permisos por DocType para roles personalizados
Story 8.1: Refinamiento de Gestión de Usuarios y Roles

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


# Matriz de permisos por rol y DocType
# Formato: {doctype: {role: [permisos]}}
# Permisos: R=Read, W=Write, C=Create, D=Delete, S=Submit, X=Cancel
PERMISSIONS_MATRIX = {
    "Prescription": {
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
        "Farmacéutico": ["R", "W"],  # Solo campos no críticos
        "Auxiliar": ["R"],
        "Bodeguero": ["R", "W"],  # Solo campos de inventario
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
    }
}


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
        
        # Configurar valores de permisos
        # Nota: Submit/Cancel/Amend requieren Write, y solo aplican si el DocType es submittable
        perm_values = {
            "read": "R" in permissions,
            "write": "W" in permissions,
            "create": "C" in permissions,
            "delete": "D" in permissions,
            "submit": "S" in permissions and is_submittable and "W" in permissions,  # Requiere Write y ser submittable
            "cancel": "X" in permissions and is_submittable and "W" in permissions,  # Requiere Write y ser submittable
            "amend": False,  # Por defecto no permitir modificar documentos enviados
            "report": "R" in permissions,  # Si puede leer, puede ver reportes
            "export": "R" in permissions,  # Si puede leer, puede exportar
            "share": False,  # Por defecto no compartir
            "print": "R" in permissions,  # Si puede leer, puede imprimir
            "email": False,  # Por defecto no enviar por email
            "import": False  # Por defecto no importar
        }
        
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


def setup_permissions_for_role(role_name):
    """Configurar permisos para un rol específico"""
    logger.info(f"Configurando permisos para rol: {role_name}")
    
    configured = 0
    skipped = 0
    
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


def setup_all_permissions():
    """Configurar permisos para todos los roles personalizados"""
    roles = [
        "Farmacéutico",
        "Auxiliar",
        "Bodeguero",
        "Administrativo",
        "Contabilidad",
        "Informática"
    ]
    
    logger.info("=== Configuración de Permisos por Rol ===")
    
    total_configured = 0
    total_skipped = 0
    
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            logger.warning(f"Rol '{role_name}' no existe, omitiendo")
            continue
        
        configured, skipped = setup_permissions_for_role(role_name)
        total_configured += configured
        total_skipped += skipped
    
    logger.info(f"Resumen: {total_configured} permisos configurados, {total_skipped} omitidos")
    
    frappe.db.commit()


if __name__ == "__main__":
    # Para ejecución manual desde consola
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "barriofarma.localhost"
    
    frappe.init(site=site)
    frappe.connect()
    
    logger.info("=" * 60)
    logger.info("Setup de Permisos por DocType - Story 8.1")
    logger.info("=" * 60)
    
    setup_all_permissions()
    
    logger.info("=" * 60)
    logger.info("✓ Configuración de permisos completada")
    logger.info("=" * 60)
    
    frappe.db.close()

