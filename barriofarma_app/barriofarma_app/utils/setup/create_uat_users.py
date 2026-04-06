# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Script para crear usuarios UAT y POS Profile asociado al auxiliar (rol cajero en E2E UI, repo barriofarma-e2e).

Uso:
    bench --site uat.barriofarma.cl execute \
        barriofarma_app.barriofarma_app.utils.setup.create_uat_users.create_uat_users
"""

import frappe
from frappe import _
import logging
from frappe.utils import today, add_days

logger = logging.getLogger(__name__)


# Configuración de usuarios UAT
# Nota: Usa perfiles predefinidos para garantizar visibilidad de módulos y permisos correctos
# Si se proporciona "profile_name", se usa el sistema de perfiles (recomendado)
# Si se proporciona "roles", se usa el método manual (compatibilidad hacia atrás)
UAT_USERS = [
    {
        "email": "farmaceutico.uat@barriofarma.cl",
        "full_name": "Juan Pérez - Farmacéutico",
        "profile_name": "Perfil Farmacéutico",  # ✅ Usa perfil predefinido (recomendado)
        "username": "farmaceutico_uat",
        "password": "Farmacia2026!",  # Cambiar en producción
        "enabled": True,
        "send_welcome_email": False
    },
    {
        "email": "auxiliar.uat@barriofarma.cl",
        "full_name": "María González - Auxiliar",
        "profile_name": "Perfil Auxiliar",  # ✅ Usa perfil predefinido
        "username": "auxiliar_uat",
        "password": "Auxiliar2026!",  # Cambiar en producción
        "enabled": True,
        "send_welcome_email": False
    },
    {
        "email": "administrativo.uat@barriofarma.cl",
        "full_name": "Ana Martínez - Administrativo",
        "profile_name": "Perfil Contabilidad",  # ✅ Usa perfil predefinido
        "username": "administrativo_uat",
        "password": "Admin2026!",  # Cambiar en producción
        "enabled": True,
        "send_welcome_email": False
    },
    {
        "email": "bodeguero.uat@barriofarma.cl",
        "full_name": "Carlos López - Bodeguero",
        "profile_name": "Perfil Bodeguero",
        "username": "bodeguero_uat",
        "password": "Bodeguero2026!",  # Cambiar en producción
        "enabled": True,
        "send_welcome_email": False
    }
]

# POS Profile para E2E (cy.loginAs('cajero') usa auxiliar UAT)
UAT_POS_PROFILE_NAME = "BarrioFarma UAT POS"


def ensure_uat_pos_profile_for_auxiliar():
    """
    Crea o actualiza el POS Profile UAT y vincula al usuario auxiliar (mismo que cajero/vendedor en pruebas E2E).
    Idempotente. Se invoca al final de create_uat_users().
    """
    auxiliar = next((u for u in UAT_USERS if u.get("username") == "auxiliar_uat"), None)
    if not auxiliar:
        logger.warning("No hay auxiliar_uat en UAT_USERS; se omite POS Profile")
        return

    user_email = auxiliar["email"]
    user_name = frappe.db.get_value("User", {"email": user_email}, "name")
    if not user_name:
        logger.warning(
            "Usuario auxiliar UAT (%s) no existe aún; se omite POS Profile", user_email
        )
        return

    frappe.set_user("Administrator")

    if not frappe.db.exists("POS Profile", UAT_POS_PROFILE_NAME):
        company = frappe.defaults.get_global_default("company")
        if not company:
            companies = frappe.get_all("Company", limit=1)
            company = companies[0].name if companies else None
        if not company:
            logger.error("ensure_uat_pos_profile_for_auxiliar: no hay Company")
            return

        warehouse = frappe.db.get_value(
            "Warehouse", {"company": company, "is_group": 0}, "name"
        )
        if not warehouse:
            warehouses = frappe.get_all("Warehouse", filters={"is_group": 0}, limit=1)
            warehouse = warehouses[0].name if warehouses else None
        if not warehouse:
            logger.error("ensure_uat_pos_profile_for_auxiliar: no hay Warehouse")
            return

        price_list = (
            frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name")
            or "Standard Selling"
        )
        write_off_account = frappe.db.get_value(
            "Account",
            {"company": company, "account_type": "Expense Account"},
            "name",
        )
        write_off_cost_center = frappe.db.get_value(
            "Cost Center", {"company": company, "is_group": 0}, "name"
        )

        pos_profile = frappe.get_doc(
            {
                "doctype": "POS Profile",
                "name": UAT_POS_PROFILE_NAME,
                "company": company,
                "warehouse": warehouse,
                "selling_price_list": price_list,
                "currency": frappe.db.get_value("Company", company, "default_currency")
                or "CLP",
                "write_off_account": write_off_account,
                "write_off_cost_center": write_off_cost_center,
            }
        )
        pos_profile.append("applicable_for_users", {"user": user_name, "default": 1})
        pos_profile.insert(ignore_permissions=True)
        frappe.db.commit()
        logger.info(
            "POS Profile creado: %s (usuario %s)", UAT_POS_PROFILE_NAME, user_name
        )
        return

    pos_profile = frappe.get_doc("POS Profile", UAT_POS_PROFILE_NAME)
    users_linked = [row.user for row in pos_profile.applicable_for_users]
    if user_name not in users_linked:
        pos_profile.append("applicable_for_users", {"user": user_name, "default": 1})
        pos_profile.save(ignore_permissions=True)
        frappe.db.commit()
        logger.info(
            "Usuario %s agregado a POS Profile %s", user_name, UAT_POS_PROFILE_NAME
        )
    else:
        logger.info(
            "Usuario %s ya está en POS Profile %s", user_name, UAT_POS_PROFILE_NAME
        )


def create_uat_user(user_config):
    """
    Crear un usuario UAT con configuración específica
    
    Soporta dos modos:
    1. Con perfil (recomendado): Si se proporciona "profile_name", usa setup_user_from_profile
       - Garantiza visibilidad de módulos
       - Configura permisos automáticamente
       - Asigna roles personalizados y estándar
    2. Manual (compatibilidad): Si se proporciona "roles", usa método manual
       - Solo asigna roles especificados
       - No garantiza visibilidad de módulos
    
    Args:
        user_config: Diccionario con configuración del usuario
            - profile_name (str, opcional): Nombre del perfil predefinido (recomendado)
            - roles (list, opcional): Lista de roles para asignar manualmente (compatibilidad)
            - email (str, requerido): Email del usuario
            - full_name (str, requerido): Nombre completo
            - username (str, requerido): Username
            - password (str, opcional): Contraseña
            - enabled (bool, opcional): Si el usuario está habilitado
    
    Returns:
        User document creado o existente
    """
    frappe.set_user("Administrator")
    
    email = user_config["email"]
    full_name = user_config["full_name"]
    username = user_config.get("username", email.split("@")[0])
    password = user_config.get("password", "TempPass123!")
    enabled = user_config.get("enabled", True)
    
    # ✅ MODO 1: Usar perfil predefinido (recomendado)
    if "profile_name" in user_config and user_config["profile_name"]:
        logger.info(f"Creando usuario '{username}' con perfil '{user_config['profile_name']}'...")
        
        try:
            from barriofarma_app.barriofarma_app.utils.permissions.setup_user_profiles import setup_user_from_profile
            
            # Crear usuario con perfil
            result = setup_user_from_profile(
                email=email,
                profile_name=user_config["profile_name"],
                full_name=full_name,
                enabled=enabled
            )
            
            if not result.get("success"):
                raise Exception(result.get("error", "Error desconocido al crear usuario con perfil"))
            
            # Obtener usuario creado
            user = frappe.get_doc("User", result["user"])
            
            # Actualizar username si es diferente
            if user.name != username:
                logger.info(f"  Actualizando username de '{user.name}' a '{username}'")
                # Nota: En Frappe, el username es el name del User, no se puede cambiar fácilmente
                # Si es necesario cambiar, se debe crear un nuevo usuario o usar el email como username
                logger.warning(f"  Username '{username}' no coincide con '{user.name}'. Usando '{user.name}' como username.")
            
            # Asignar contraseña
            if password:
                user.new_password = password
                user.save(ignore_permissions=True)
                frappe.db.commit()
            
            # Limpiar cache de permisos
            frappe.clear_cache(user=user.name)
            
            logger.info(f"✓ Usuario '{user.name}' creado/actualizado con perfil '{user_config['profile_name']}'")
            logger.info(f"  Módulos visibles: {', '.join(result.get('visible_modules', []))}")
            logger.info(f"  Roles agregados: {', '.join(result.get('roles_added', []))}")
            
            return user
            
        except ImportError:
            logger.warning("No se pudo importar setup_user_profiles, usando método manual")
            # Continuar con método manual
        except Exception as e:
            logger.error(f"Error al crear usuario con perfil: {str(e)}")
            logger.warning("Intentando método manual como fallback...")
            # Continuar con método manual
    
    # ⚠️ MODO 2: Método manual (compatibilidad hacia atrás)
    logger.info(f"Creando usuario '{username}' con método manual...")
    
    roles = user_config.get("roles", [user_config.get("role")])  # Soporta múltiples roles o rol único
    if isinstance(roles, str):
        roles = [roles]  # Convertir a lista si es string
    
    # Extraer first_name y last_name de full_name
    name_parts = full_name.split(" - ", 1)  # Separar nombre y rol
    actual_name = name_parts[0] if name_parts else full_name
    name_split = actual_name.split(" ", 1)
    first_name = name_split[0] if name_split else actual_name
    last_name = name_split[1] if len(name_split) > 1 else ""
    
    # Verificar si usuario ya existe por username o email
    existing_username = frappe.db.exists("User", username)
    existing_email = frappe.db.get_value("User", {"email": email}, "name")
    
    if existing_username:
        logger.info(f"Usuario '{username}' ya existe, actualizando...")
        user = frappe.get_doc("User", username)
    elif existing_email:
        logger.info(f"Usuario con email '{email}' ya existe, actualizando...")
        user = frappe.get_doc("User", existing_email)
        # Nota: En Frappe, el username (name) no se puede cambiar fácilmente
        # Si username es diferente, se usa el existente
        if user.name != username:
            logger.warning(f"  Username esperado '{username}' pero usuario existe como '{user.name}'. Usando '{user.name}'.")
    else:
        logger.info(f"Creando usuario '{username}'...")
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "enabled": enabled,
            "send_welcome_email": False,
            "user_type": "System User"
        })
        user.insert(ignore_permissions=True)
        # Actualizar username después de insertar si es necesario
        if user.name != username:
            logger.warning(f"  Username generado '{user.name}' difiere del esperado '{username}'. Usando '{user.name}'.")
    
    # Actualizar configuración
    user.enabled = enabled
    user.send_welcome_email = False
    # Actualizar nombres y email
    user.first_name = first_name
    user.last_name = last_name
    user.full_name = full_name
    if user.email != email:
        user.email = email
    
    # Asignar contraseña
    if password:
        user.new_password = password
    
    # Guardar usuario
    user.save(ignore_permissions=True)
    frappe.db.commit()
    
    # Asignar roles (múltiples roles soportados)
    roles_added = []
    for role in roles:
        if not frappe.db.exists("Has Role", {"parent": user.name, "role": role}):
            user.append("roles", {
                "role": role
            })
            roles_added.append(role)
    
    if roles_added:
        user.save(ignore_permissions=True)
        frappe.db.commit()
        logger.info(f"  Roles asignados: {', '.join(roles_added)}")
    else:
        logger.info(f"  No se agregaron nuevos roles (ya existían o no se especificaron)")
    
    # Limpiar cache de permisos
    frappe.clear_cache(user=user.name)
    
    logger.info(f"✓ Usuario '{user.name}' creado/actualizado exitosamente (método manual)")
    logger.warning(f"  ⚠️  Nota: Método manual no garantiza visibilidad de módulos. Considera usar 'profile_name'.")
    
    return user


def create_uat_users():
    """
    Crear todos los usuarios UAT definidos en UAT_USERS
    """
    logger.info("=" * 60)
    logger.info("CREACIÓN DE USUARIOS UAT")
    logger.info("=" * 60)
    
    frappe.set_user("Administrator")
    
    created = []
    errors = []
    
    for user_config in UAT_USERS:
        try:
            user = create_uat_user(user_config)
            
            # Obtener información del usuario creado
            user_info = {
                "username": user.name,
                "email": user.email,
                "password": user_config.get("password", "N/A")
            }
            
            # Si usó perfil, incluir información del perfil
            if "profile_name" in user_config and user_config.get("profile_name"):
                user_info["profile"] = user_config["profile_name"]
                # Obtener roles del usuario
                roles = frappe.get_all("Has Role",
                    filters={"parent": user.name},
                    fields=["role"]
                )
                user_info["roles"] = [r["role"] for r in roles]
            else:
                # Método manual: usar roles de la configuración
                roles = user_config.get("roles", [user_config.get("role")])
                if isinstance(roles, str):
                    roles = [roles]
                user_info["roles"] = roles
            
            created.append(user_info)
        except Exception as e:
            username = user_config.get("username", user_config.get("email", "desconocido"))
            error_msg = f"Error creando usuario '{username}': {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Resumen
    logger.info("\n" + "-" * 60)
    logger.info("RESUMEN")
    logger.info("-" * 60)
    
    if created:
        logger.info(f"\nUsuarios creados/actualizados ({len(created)}):")
        for user in created:
            roles_str = ", ".join(user['roles']) if isinstance(user['roles'], list) else user['roles']
            profile_info = f" - Perfil: {user.get('profile', 'Manual')}" if 'profile' in user else ""
            logger.info(f"  - {user['username']} ({user['email']}){profile_info}")
            logger.info(f"    Roles: {roles_str}")
            logger.info(f"    Contraseña: {user['password']}")
    
    if errors:
        logger.error(f"\nErrores ({len(errors)}):")
        for error in errors:
            logger.error(f"  - {error}")
    
    logger.info("=" * 60)
    
    frappe.db.commit()

    try:
        ensure_uat_pos_profile_for_auxiliar()
    except Exception as e:
        logger.warning("ensure_uat_pos_profile_for_auxiliar falló (POS puede requerir setup manual): %s", e)
    
    return {
        "created": created,
        "errors": errors
    }


def list_uat_users():
    """
    Listar usuarios UAT existentes
    """
    logger.info("=" * 60)
    logger.info("USUARIOS UAT EXISTENTES")
    logger.info("=" * 60)
    
    users = frappe.get_all("User", 
        filters={"username": ("in", [u["username"] for u in UAT_USERS])},
        fields=["name", "email", "full_name", "enabled"]
    )
    
    for user in users:
        # Obtener roles
        roles = frappe.get_all("Has Role",
            filters={"parent": user.name},
            fields=["role"]
        )
        role_names = [r["role"] for r in roles]
        
        status = "activo" if user.enabled else "deshabilitado"
        logger.info(f"\n{user.full_name} ({user.name})")
        logger.info(f"  Email: {user.email}")
        logger.info(f"  Roles: {', '.join(role_names)}")
        logger.info(f"  Estado: {status}")
    
    logger.info("=" * 60)
    
    return users


def delete_uat_user(username):
    """
    Eliminar un usuario UAT específico
    
    Args:
        username: Nombre de usuario a eliminar (puede ser username o cualquier nombre de usuario UAT)
    
    Returns:
        True si se eliminó exitosamente, False en caso contrario
    """
    frappe.set_user("Administrator")
    
    if not frappe.db.exists("User", username):
        logger.warning(f"Usuario '{username}' no existe")
        return False
    
    try:
        # Obtener email del usuario para verificar que es UAT
        user_email = frappe.db.get_value("User", username, "email")
        uat_emails = [u["email"] for u in UAT_USERS]
        
        # Verificar que es un usuario UAT por email o username
        uat_usernames = [u["username"] for u in UAT_USERS]
        is_uat_user = (username in uat_usernames) or (user_email in uat_emails)
        
        if not is_uat_user:
            logger.warning(f"Usuario '{username}' (email: {user_email}) no es un usuario UAT definido")
            return False
        
        # Eliminar usuario
        frappe.delete_doc("User", username, force=True, ignore_permissions=True)
        frappe.db.commit()
        
        # Limpiar cache
        frappe.clear_cache(user=username)
        
        logger.info(f"✓ Usuario '{username}' eliminado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error eliminando usuario '{username}': {str(e)}")
        frappe.db.rollback()
        return False


def delete_uat_users():
    """
    Eliminar todos los usuarios UAT definidos en UAT_USERS
    Busca por username y también por email para encontrar usuarios existentes
    """
    logger.info("=" * 60)
    logger.info("ELIMINACIÓN DE USUARIOS UAT")
    logger.info("=" * 60)
    
    frappe.set_user("Administrator")
    
    deleted = []
    errors = []
    skipped = []
    
    for user_config in UAT_USERS:
        username = user_config["username"]
        email = user_config["email"]
        
        # Buscar por username primero
        user_found = None
        if frappe.db.exists("User", username):
            user_found = username
        else:
            # Buscar por email
            existing_email_user = frappe.db.get_value("User", {"email": email}, "name")
            if existing_email_user:
                user_found = existing_email_user
                logger.info(f"  Usuario encontrado por email: {existing_email_user} (email: {email})")
        
        if not user_found:
            skipped.append(f"{username} (no existe)")
            logger.info(f"  Omitido: {username} (no existe)")
            continue
        
        try:
            if delete_uat_user(user_found):
                deleted.append(user_found)
            else:
                errors.append(f"{user_found} (error al eliminar)")
        except Exception as e:
            error_msg = f"Error eliminando usuario '{user_found}': {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Resumen
    logger.info("\n" + "-" * 60)
    logger.info("RESUMEN")
    logger.info("-" * 60)
    
    if deleted:
        logger.info(f"\nUsuarios eliminados ({len(deleted)}):")
        for username in deleted:
            logger.info(f"  - {username}")
    
    if skipped:
        logger.info(f"\nUsuarios omitidos ({len(skipped)}):")
        for username in skipped:
            logger.info(f"  - {username}")
    
    if errors:
        logger.error(f"\nErrores ({len(errors)}):")
        for error in errors:
            logger.error(f"  - {error}")
    
    logger.info("=" * 60)
    
    frappe.db.commit()
    
    return {
        "deleted": deleted,
        "skipped": skipped,
        "errors": errors
    }


def verify_uat_users_roles():
    """
    Verificar roles asignados a usuarios UAT
    """
    print("=" * 60)
    print("VERIFICACIÓN DE ROLES DE USUARIOS UAT")
    print("=" * 60)
    
    frappe.set_user("Administrator")
    
    users = frappe.get_all("User", 
        filters={"username": ("in", [u["username"] for u in UAT_USERS])},
        fields=["name", "email", "full_name", "enabled"]
    )
    
    for user in users:
        # Obtener roles
        roles = frappe.get_all("Has Role",
            filters={"parent": user.name},
            fields=["role"]
        )
        role_names = [r["role"] for r in roles]
        
        # Obtener roles esperados de la configuración (buscar por username o email)
        user_config = next((u for u in UAT_USERS if u["username"] == user.name or u["email"] == user.email), None)
        if user_config:
            expected_roles = user_config.get("roles", [])
            if not expected_roles and "role" in user_config:
                expected_roles = [user_config["role"]]
            if isinstance(expected_roles, str):
                expected_roles = [expected_roles]
        else:
            expected_roles = []
        
        status = "activo" if user.enabled else "deshabilitado"
        print(f"\n{user.full_name} ({user.name})")
        print(f"  Email: {user.email}")
        print(f"  Estado: {status}")
        print(f"  Roles asignados: {', '.join(role_names) if role_names else 'Ninguno'}")
        print(f"  Roles esperados: {', '.join(expected_roles)}")
        
        # Verificar que todos los roles esperados están asignados
        missing_roles = set(expected_roles) - set(role_names)
        if missing_roles:
            print(f"  ⚠️  Roles faltantes: {', '.join(missing_roles)}")
        else:
            print(f"  ✓ Todos los roles están asignados correctamente")
    
    print("=" * 60)
    
    return users


if __name__ == "__main__":
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "frontend"
    
    frappe.init(site=site)
    frappe.connect()
    
    create_uat_users()
    verify_uat_users_roles()
    
    frappe.db.close()
