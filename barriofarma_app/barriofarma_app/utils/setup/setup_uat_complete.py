# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Script maestro para configuración completa del ambiente UAT
Ejecuta todos los pasos necesarios para ambientar UAT en el orden correcto

Uso:
    bench --site uat.barriofarma.cl execute \
        barriofarma_app.barriofarma_app.utils.setup.setup_uat_complete.setup_uat_complete
"""

import frappe
from frappe import _
import logging

logger = logging.getLogger(__name__)


def setup_uat_complete(skip_migration=False, skip_users=False, skip_data=False, skip_validation=False):
    """
    Ejecutar configuración completa del ambiente UAT
    
    Args:
        skip_migration (bool): Si True, omite la migración (asume que ya se ejecutó)
        skip_users (bool): Si True, omite la creación de usuarios
        skip_data (bool): Si True, omite la carga de datos
        skip_validation (bool): Si True, omite la validación final
    
    Returns:
        dict: Resumen de la ejecución
    """
    logger.info("=" * 70)
    logger.info("CONFIGURACIÓN COMPLETA DEL AMBIENTE UAT")
    logger.info("=" * 70)
    
    results = {
        "migration": None,
        "roles": None,
        "permissions": None,
        "users": None,
        "data": None,
        "validation": None,
        "errors": []
    }
    
    frappe.set_user("Administrator")
    
    # Paso 1: Migración (si no se omite)
    if not skip_migration:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 1: Ejecutando migración...")
        logger.info("-" * 70)
        try:
            # La migración ejecuta automáticamente setup_roles y setup_permissions
            # a través del hook after_migrate
            logger.info("NOTA: Ejecutar 'bench --site <site> migrate' manualmente")
            logger.info("La migración ejecuta automáticamente:")
            logger.info("  - setup_roles.create_custom_roles()")
            logger.info("  - setup_permissions.setup_all_permissions()")
            results["migration"] = "skipped_manual"
        except Exception as e:
            error_msg = f"Error en migración: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["migration"] = "error"
    else:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 1: Migración omitida (skip_migration=True)")
        logger.info("-" * 70)
        results["migration"] = "skipped"
    
    # Paso 2: Verificar/Crear roles (si la migración se omitió)
    if skip_migration:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 2: Verificando/Creando roles personalizados...")
        logger.info("-" * 70)
        try:
            from barriofarma_app.barriofarma_app.utils.permissions.setup_roles import create_custom_roles, verify_roles
            
            # Verificar roles existentes
            all_exist = verify_roles()
            
            if not all_exist:
                # Crear roles faltantes
                created = create_custom_roles()
                if created:
                    logger.info(f"Roles creados: {', '.join(created)}")
                results["roles"] = {"created": created, "all_exist": all_exist}
            else:
                logger.info("Todos los roles ya existen")
                results["roles"] = {"created": [], "all_exist": True}
        except Exception as e:
            error_msg = f"Error creando roles: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["roles"] = "error"
    else:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 2: Roles configurados automáticamente en migración")
        logger.info("-" * 70)
        results["roles"] = "auto"
    
    # Paso 3: Configurar permisos (si la migración se omitió)
    if skip_migration:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 3: Configurando permisos...")
        logger.info("-" * 70)
        try:
            from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import setup_all_permissions
            
            setup_all_permissions(use_extended_strategy=True)
            logger.info("Permisos configurados correctamente")
            results["permissions"] = "success"
        except Exception as e:
            error_msg = f"Error configurando permisos: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["permissions"] = "error"
    else:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 3: Permisos configurados automáticamente en migración")
        logger.info("-" * 70)
        results["permissions"] = "auto"
    
    # Paso 4: Crear usuarios UAT
    if not skip_users:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 4: Creando usuarios UAT...")
        logger.info("-" * 70)
        try:
            from barriofarma_app.barriofarma_app.utils.setup.create_uat_users import create_uat_users
            
            users_result = create_uat_users()
            results["users"] = users_result
            logger.info(f"Usuarios creados: {len(users_result.get('created', []))}")
            if users_result.get('errors'):
                logger.warning(f"Errores: {len(users_result.get('errors', []))}")
        except Exception as e:
            error_msg = f"Error creando usuarios: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["users"] = "error"
    else:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 4: Creación de usuarios omitida (skip_users=True)")
        logger.info("-" * 70)
        results["users"] = "skipped"
    
    # Paso 5: Cargar datos de prueba
    if not skip_data:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 5: Cargando datos de prueba...")
        logger.info("-" * 70)
        try:
            from barriofarma_app.barriofarma_app.utils.setup.load_uat_data import load_test_data
            
            data_result = load_test_data()
            results["data"] = data_result
            logger.info("Datos cargados exitosamente")
        except Exception as e:
            error_msg = f"Error cargando datos: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["data"] = "error"
    else:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 5: Carga de datos omitida (skip_data=True)")
        logger.info("-" * 70)
        results["data"] = "skipped"
    
    # Paso 6: Validar configuración
    if not skip_validation:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 6: Validando configuración...")
        logger.info("-" * 70)
        try:
            from barriofarma_app.barriofarma_app.utils.setup.validate_uat_flows import validate_all_flows
            
            validation_result = validate_all_flows()
            results["validation"] = validation_result
            
            # Contar tests pasados/fallidos
            total_passed = sum(len(r.get("passed", [])) for r in validation_result.values() if isinstance(r, dict))
            total_failed = sum(len(r.get("failed", [])) for r in validation_result.values() if isinstance(r, dict))
            
            logger.info(f"Tests pasados: {total_passed}")
            if total_failed > 0:
                logger.warning(f"Tests fallidos: {total_failed}")
            else:
                logger.info("✓ Todos los tests pasaron")
        except Exception as e:
            error_msg = f"Error en validación: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["validation"] = "error"
    else:
        logger.info("\n" + "-" * 70)
        logger.info("PASO 6: Validación omitida (skip_validation=True)")
        logger.info("-" * 70)
        results["validation"] = "skipped"
    
    # Resumen final
    logger.info("\n" + "=" * 70)
    logger.info("RESUMEN DE CONFIGURACIÓN")
    logger.info("=" * 70)
    
    logger.info(f"Migración: {results['migration']}")
    logger.info(f"Roles: {results['roles']}")
    logger.info(f"Permisos: {results['permissions']}")
    logger.info(f"Usuarios: {results['users']}")
    logger.info(f"Datos: {results['data']}")
    logger.info(f"Validación: {results['validation']}")
    
    if results["errors"]:
        logger.error(f"\nErrores encontrados ({len(results['errors'])}):")
        for error in results["errors"]:
            logger.error(f"  - {error}")
    else:
        logger.info("\n✓ Configuración completada sin errores")
    
    logger.info("=" * 70)
    
    frappe.db.commit()
    
    return results


if __name__ == "__main__":
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "frontend"
    
    frappe.init(site=site)
    frappe.connect()
    
    # Ejecutar configuración completa
    # Para omitir migración (si ya se ejecutó): skip_migration=True
    setup_uat_complete(
        skip_migration=False,  # Cambiar a True si la migración ya se ejecutó
        skip_users=False,
        skip_data=False,
        skip_validation=False
    )
    
    frappe.db.close()
