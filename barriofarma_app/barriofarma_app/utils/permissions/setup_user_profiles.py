# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Script para automatizar la configuración de usuarios con perfiles de roles
y visibilidad de módulos basado en perfiles de referencia.

ESTRATEGIA:
1. Definir perfiles de usuario (ej: "Perfil Operativo" → Compras, Ventas, Almacén, CRM, Herramientas)
2. Mapear módulos visibles a roles estándar de ERPNext necesarios
3. Asignar roles personalizados + roles estándar según perfil
4. Automatizar creación/actualización de usuarios con perfiles

Uso:
    bench --site barriofarma.localhost execute \
        barriofarma_app.barriofarma_app.utils.permissions.setup_user_profiles.analyze_user_profile \
        --user natalia.araya@barriofarma.cl

    bench --site frontend execute \
        barriofarma_app.barriofarma_app.utils.permissions.setup_user_profiles.setup_user_from_profile \
        --email nuevo.usuario@barriofarma.cl \
        --profile "Perfil Operativo"
"""

import frappe
from frappe import _
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# MAPEO DE MÓDULOS A ROLES ESTÁNDAR DE ERPNEXT
# ============================================================================
# En Frappe/ERPNext, los módulos visibles en el menú se determinan por
# roles estándar que tienen módulos asociados implícitamente.
# Este mapeo define qué roles estándar activan qué módulos.

MODULE_TO_STANDARD_ROLES = {
    "Buying": ["Purchase Manager", "Purchase User"],  # Compras
    "Selling": ["Sales Manager", "Sales User"],  # Ventas
    "Stock": ["Stock Manager", "Stock User"],  # Almacén
    "Accounts": ["Accounts Manager", "Accounts User"],  # Contabilidad
    "CRM": ["CRM User"],  # CRM
    "Tools": ["System Manager"],  # Herramientas (requiere System Manager)
    "HR": ["HR Manager", "HR User"],  # Recursos Humanos
    "Manufacturing": ["Manufacturing Manager", "Manufacturing User"],  # Manufactura
    "Projects": ["Project Manager"],  # Proyectos
}

# Roles estándar mínimos recomendados por módulo (menos permisos)
MODULE_TO_MINIMAL_ROLES = {
    "Buying": ["Purchase User"],  # Solo lectura/operación básica
    "Selling": ["Sales User"],
    "Stock": ["Stock User"],
    "Accounts": ["Accounts User"],
    "CRM": ["CRM User"],
    "Tools": ["System Manager"],  # Tools requiere System Manager
    "HR": ["HR User"],
    "Manufacturing": ["Manufacturing User"],
    "Projects": ["Project Manager"],
}


# ============================================================================
# PERFILES DE USUARIO PREDEFINIDOS
# ============================================================================
# Define qué módulos debe ver cada perfil y qué roles personalizados incluir

PROTECTED_USER_ROLES = frozenset({"All", "Guest", "Desk User", "System User"})

# Roles estándar ERPNext para administración y contabilidad (pagos, plan de cuentas, facturas).
ADMIN_ERPNEXT_STANDARD_ROLES = (
    "Accounts Manager",
    "Accounts User",
    "Purchase Manager",
    "Purchase User",
    "Sales User",
    "Stock User",
)

ADMIN_ERPNEXT_STANDARD_ROLES_CONTABILIDAD = (
    "Accounts Manager",
    "Accounts User",
    "Purchase User",
    "Sales User",
)

# Roles que setup_user_from_profile puede quitar al re-aplicar un perfil
MANAGED_STANDARD_ROLES = frozenset({
    "Purchase User",
    "Purchase Manager",
    "Sales User",
    "Sales Master Manager",
    "Sales Manager",
    "Stock User",
    "Stock Manager",
    "Accounts User",
    "Accounts Manager",
    "CRM User",
    "System Manager",
    "Dashboard Manager",
    "Workspace Manager",
}) | frozenset(ADMIN_ERPNEXT_STANDARD_ROLES)

USER_PROFILES = {
    "Perfil Operativo": {
        "description": "Perfil para usuarios operativos (ej: Natalia Araya)",
        "visible_modules": ["Buying", "Selling", "Stock"],
        "extra_modules": ["Setup"],
        "extra_desktop_icons": ["Organization"],
        "custom_roles": ["Farmacéutico"],
        "standard_roles": [],
        "use_minimal_roles": True,
    },
    "Perfil Farmacéutico": {
        "description": "Farmacéutico: compras (PO, RFQ, cotizaciones, MR), maestros producto/precios, QC/submit PR, POS, reconciliación inventario",
        "visible_modules": ["Buying", "Selling", "Stock"],
        "extra_modules": ["Setup"],
        "extra_desktop_icons": ["Organization"],
        "custom_roles": ["Farmacéutico"],
        "standard_roles": [],
        "use_minimal_roles": True,
    },
    "Perfil Bodeguero": {
        "description": "Perfil para bodegueros - acceso a compras y almacén",
        "visible_modules": ["Buying", "Stock"],
        "custom_roles": ["Bodeguero"],
        "standard_roles": ["Purchase User", "Stock User"],
        "use_minimal_roles": True,
    },
    "Perfil Contabilidad": {
        "description": "Contabilidad: roles ERPNext Accounts Manager/User; pagos, asientos y plan de cuentas.",
        "visible_modules": ["Accounts", "Selling", "Buying"],
        "visible_accounts_desktop": True,
        "custom_roles": ["Contabilidad"],
        "standard_roles": list(ADMIN_ERPNEXT_STANDARD_ROLES_CONTABILIDAD),
        "use_minimal_roles": False,
        "permissions_via_erpnext_standard": True,
    },
    "Perfil Administrativo": {
        "description": "Administración (Karla/Jimena): ERPNext Accounts Manager, compras, pagos OC, plan de cuentas, almacén y ventas.",
        "visible_modules": ["Selling", "Buying", "Stock", "Accounts"],
        "visible_accounts_desktop": True,
        "custom_roles": ["Administrativo", "Contabilidad"],
        "standard_roles": list(ADMIN_ERPNEXT_STANDARD_ROLES),
        "use_minimal_roles": False,
        "permissions_via_erpnext_standard": True,
    },
    "Perfil Auxiliar": {
        "description": "Auxiliar: PR borrador, POS, Stock Entry, Reconciliación de inventarios, Shelf Movement, reportes de existencias; sin submit PR",
        "visible_modules": ["Selling", "Stock"],
        "extra_modules": ["Setup"],
        "extra_desktop_icons": ["Organization"],
        "custom_roles": ["Auxiliar"],
        "standard_roles": [],
        "use_minimal_roles": True,
    },
    "Perfil Informática": {
        "description": (
            "Administrador plataforma BarrioFarma (Eduardo): KPIs Desk, workspaces públicos, "
            "gestión de usuarios/perfiles; revisión operativa compras/ventas/stock/contabilidad."
        ),
        "visible_modules": ["Buying", "Selling", "Stock", "Accounts"],
        "extra_modules": ["Setup"],
        "extra_desktop_icons": ["Organization"],
        "custom_roles": ["Informática"],
        "standard_roles": [
            "Dashboard Manager",
            "Workspace Manager",
            "System Manager",
        ],
        "use_minimal_roles": False,
    },
}


def analyze_user_profile(user_email):
    """
    Analiza la configuración actual de un usuario y genera un perfil basado en:
    - Roles asignados
    - Módulos visibles (inferidos de roles estándar)
    - Permisos en DocTypes clave
    
    Args:
        user_email: Email del usuario a analizar
        
    Returns:
        dict: Perfil generado con roles y módulos detectados
    """
    frappe.set_user("Administrator")
    
    if not frappe.db.exists("User", {"email": user_email}):
        logger.error(f"Usuario {user_email} no existe")
        return None
    
    user = frappe.get_doc("User", {"email": user_email})
    
    print("=" * 70)
    print(f"ANÁLISIS DE PERFIL: {user.full_name or user.name}")
    print("=" * 70)
    print(f"Email: {user.email}")
    print(f"Estado: {'Activo' if user.enabled else 'Deshabilitado'}")
    
    # Obtener roles asignados
    user_roles = frappe.get_all("Has Role",
        filters={"parent": user.name},
        fields=["role"],
        order_by="role"
    )
    role_names = [r.role for r in user_roles]
    
    print(f"\nRoles asignados ({len(role_names)}):")
    for role in role_names:
        role_doc = frappe.get_doc("Role", role)
        desk_access = getattr(role_doc, "desk_access", 0)
        is_custom = getattr(role_doc, "is_custom", 0)
        role_type = "Personalizado" if is_custom else "Estándar"
        print(f"  - {role} [{role_type}] - desk_access={desk_access}")
    
    # Inferir módulos visibles de roles estándar
    visible_modules = set()
    standard_roles_detected = []
    custom_roles_detected = []
    
    for role_name in role_names:
        role_doc = frappe.get_doc("Role", role_name)
        is_custom = getattr(role_doc, "is_custom", 0)
        
        # Verificar si es rol personalizado de Barriofarma
        # Los roles personalizados de Barriofarma no están en roles estándar de ERPNext
        is_barriofarma_custom = role_name in ["Farmacéutico", "Auxiliar", "Bodeguero", "Administrativo", "Contabilidad", "Informática"]
        
        if is_custom or is_barriofarma_custom:
            custom_roles_detected.append(role_name)
        else:
            standard_roles_detected.append(role_name)
            # Buscar módulo asociado
            for module, roles in MODULE_TO_STANDARD_ROLES.items():
                if role_name in roles:
                    visible_modules.add(module)
    
    print(f"\nMódulos visibles inferidos ({len(visible_modules)}):")
    for module in sorted(visible_modules):
        print(f"  - {module}")
    
    print(f"\nRoles personalizados: {', '.join(custom_roles_detected) if custom_roles_detected else 'Ninguno'}")
    print(f"Roles estándar: {', '.join(standard_roles_detected) if standard_roles_detected else 'Ninguno'}")
    
    # Generar perfil
    profile = {
        "user_email": user_email,
        "user_name": user.full_name or user.name,
        "visible_modules": sorted(list(visible_modules)),
        "custom_roles": custom_roles_detected,
        "standard_roles": standard_roles_detected,
        "all_roles": role_names,
    }
    
    # Buscar perfil predefinido más cercano
    matching_profile = find_matching_profile(profile)
    if matching_profile:
        print(f"\nPerfil predefinido más cercano: {matching_profile}")
        profile["suggested_profile"] = matching_profile
    
    return profile


def find_matching_profile(user_profile):
    """
    Encuentra el perfil predefinido que mejor coincide con el perfil del usuario.
    
    Args:
        user_profile: Perfil generado de analyze_user_profile
        
    Returns:
        str: Nombre del perfil predefinido más cercano, o None
    """
    user_modules = set(user_profile["visible_modules"])
    user_custom_roles = set(user_profile["custom_roles"])
    
    best_match = None
    best_score = 0
    
    for profile_name, profile_config in USER_PROFILES.items():
        profile_modules = set(profile_config["visible_modules"])
        profile_custom_roles = set(profile_config["custom_roles"])
        
        # Calcular score de coincidencia
        module_match = len(user_modules & profile_modules) / max(len(user_modules | profile_modules), 1)
        role_match = len(user_custom_roles & profile_custom_roles) / max(len(user_custom_roles | profile_custom_roles), 1)
        
        score = (module_match * 0.7) + (role_match * 0.3)  # Módulos pesan más
        
        if score > best_score and score > 0.5:  # Mínimo 50% de coincidencia
            best_score = score
            best_match = profile_name
    
    return best_match


def create_or_update_module_profile(profile_name, modules, roles):
    """
    Crea o actualiza un Module Profile en Frappe para controlar visibilidad de módulos.
    
    Args:
        profile_name: Nombre del Module Profile
        modules: Lista de nombres de módulos a incluir
        roles: Lista de roles que deben tener acceso a este Module Profile
        
    Returns:
        Module Profile document creado o actualizado
    """
    frappe.set_user("Administrator")
    
    # Verificar si Module Profile existe
    if frappe.db.exists("Module Profile", profile_name):
        module_profile = frappe.get_doc("Module Profile", profile_name)
        logger.info(f"Module Profile '{profile_name}' existe, actualizando...")
    else:
        module_profile = frappe.get_doc({
            "doctype": "Module Profile",
            "module_profile_name": profile_name
        })
        module_profile.insert(ignore_permissions=True)
        logger.info(f"Module Profile '{profile_name}' creado")
    
    # Actualizar módulos (si Module Profile tiene campo modules)
    # Nota: La estructura exacta depende de cómo esté definido Module Profile
    # Por ahora, nos enfocamos en asignar roles al Module Profile
    
    # Asignar roles al Module Profile
    current_roles = set([
        r.role for r in frappe.get_all("Has Role",
            filters={"parent": module_profile.name, "parenttype": "Module Profile"},
            fields=["role"]
        )
    ])
    
    target_roles = set(roles)
    roles_to_add = target_roles - current_roles
    roles_to_remove = current_roles - target_roles
    
    if roles_to_add:
        for role_name in roles_to_add:
            if frappe.db.exists("Role", role_name):
                module_profile.append("roles", {"role": role_name})
                logger.debug(f"  + Rol '{role_name}' agregado al Module Profile")
    
    if roles_to_remove:
        module_profile.roles = [r for r in module_profile.roles if r.role not in roles_to_remove]
        for role_name in roles_to_remove:
            logger.debug(f"  - Rol '{role_name}' removido del Module Profile")
    
    if roles_to_add or roles_to_remove:
        module_profile.save(ignore_permissions=True)
        frappe.db.commit()
        logger.info(f"Module Profile '{profile_name}' actualizado con {len(target_roles)} roles")
    
    return module_profile


def setup_user_from_profile(email, profile_name, full_name=None, enabled=True, use_module_profile=True):
    """
    Configura un usuario con un perfil predefinido.
    Asigna los roles necesarios para que vea los módulos especificados.
    
    Args:
        email: Email del usuario
        profile_name: Nombre del perfil predefinido (de USER_PROFILES)
        full_name: Nombre completo del usuario (opcional)
        enabled: Si el usuario debe estar habilitado
        
    Returns:
        dict: Resultado de la configuración
    """
    frappe.set_user("Administrator")
    
    if profile_name not in USER_PROFILES:
        logger.error(f"Perfil '{profile_name}' no existe. Perfiles disponibles: {', '.join(USER_PROFILES.keys())}")
        return {"success": False, "error": f"Perfil '{profile_name}' no existe"}
    
    profile_config = USER_PROFILES[profile_name]
    
    print("=" * 70)
    print(f"CONFIGURANDO USUARIO CON PERFIL: {profile_name}")
    print("=" * 70)
    print(f"Email: {email}")
    print(f"Perfil: {profile_name}")
    print(f"Descripción: {profile_config['description']}")
    print(f"Módulos visibles: {', '.join(profile_config['visible_modules'])}")
    print(f"Roles personalizados: {', '.join(profile_config['custom_roles'])}")
    print(f"Roles estándar: {', '.join(profile_config['standard_roles'])}")
    
    # Crear o actualizar usuario
    if frappe.db.exists("User", {"email": email}):
        user = frappe.get_doc("User", {"email": email})
        print(f"\nUsuario existente encontrado: {user.name}")
    else:
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": full_name or email.split("@")[0] if full_name is None else full_name,
            "enabled": enabled,
            "send_welcome_email": False,
        })
        user.insert(ignore_permissions=True)
        print(f"\nUsuario creado: {user.name}")
    
    if full_name:
        user.full_name = full_name
    user.enabled = enabled
    user.save(ignore_permissions=True)
    
    # Obtener roles actuales
    current_roles = set([
        r.role for r in frappe.get_all("Has Role",
            filters={"parent": user.name},
            fields=["role"]
        )
    ])
    
    # Roles objetivo
    target_roles = set(profile_config["custom_roles"] + profile_config["standard_roles"])
    
    # Agregar roles faltantes
    roles_to_add = target_roles - current_roles
    roles_to_remove = (current_roles - target_roles) & MANAGED_STANDARD_ROLES
    
    print(f"\nRoles actuales: {len(current_roles)}")
    print(f"Roles objetivo: {len(target_roles)}")
    
    if roles_to_add:
        print(f"\nAgregando roles ({len(roles_to_add)}):")
        for role_name in roles_to_add:
            if not frappe.db.exists("Role", role_name):
                logger.warning(f"Rol '{role_name}' no existe, omitiendo")
                continue
            
            user.append("roles", {"role": role_name})
            print(f"  + {role_name}")
    
    if roles_to_remove:
        print(f"\nRemoviendo roles ({len(roles_to_remove)}):")
        for role_name in roles_to_remove:
            # No remover roles si están en otros perfiles o son críticos
            if role_name in PROTECTED_USER_ROLES:
                print(f"  - {role_name} (protegido, no se remueve)")
                continue
            
            # Remover de la lista de roles
            user.roles = [r for r in user.roles if r.role != role_name]
            print(f"  - {role_name}")
    
    if roles_to_add or roles_to_remove:
        user.save(ignore_permissions=True)
        frappe.db.commit()
        print("\nRoles actualizados exitosamente")
    else:
        print("\nNo se requieren cambios en roles")
    
    # Configurar módulos permitidos/bloqueados
    print("\n" + "-" * 70)
    print("CONFIGURANDO MÓDULOS PERMITIDOS:")
    print("-" * 70)
    
    try:
        # Obtener todos los módulos disponibles
        all_modules = frappe.get_all("Module Def",
            fields=["name"],
            filters={"app_name": ["in", ["erpnext", "frappe", "barriofarma_app"]]}
        )
        all_module_names = set([m["name"] for m in all_modules])
        
        # Módulos que deben estar visibles según el perfil
        # Mapear nombres de módulos del perfil a nombres reales
        module_name_mapping = {
            "Buying": "Buying",
            "Selling": "Selling",
            "Stock": "Stock",
            "CRM": "CRM",
            "Tools": "Desk",  # Tools se mapea a Desk en Frappe
            "Accounts": "Accounts",
            "Setup": "Setup",
            "HR": "HR",
            "Manufacturing": "Manufacturing",
            "Projects": "Projects"
        }
        
        # Módulos base que suelen requerirse para Desk / comunicación / app BarrioFarma.
        # No incluir aquí módulos de negocio opcionales (Calidad, Integraciones, etc.):
        # si van en base_modules, quedan visibles para todos los perfiles aunque no estén
        # en visible_modules. Esos deben bloquearse salvo que un perfil los liste explícitamente.
        base_modules = {
            "Desk",           # Herramientas base (mapeado desde Tools)
            "Workflow",       # Flujos de Trabajo
            "Customize",      # Personalizar
            "Automation",     # Automatización
            "Email",          # Correo electrónico
            "Contacts",       # Contactos
            "Communications", # Comunicaciones
            "Print",          # Impresión
            "Social",
            "Portal",
            "Geo",
            "EDI",
            "Barriofarma App"  # Barriofarma App (nombre real en la BD)
        }
        
        # Módulos permitidos = módulos del perfil + módulos base
        allowed_modules = set()
        for module in profile_config["visible_modules"]:
            mapped_name = module_name_mapping.get(module, module)
            if mapped_name in all_module_names:
                allowed_modules.add(mapped_name)

        for module in profile_config.get("extra_modules", []):
            mapped_name = module_name_mapping.get(module, module)
            if mapped_name in all_module_names:
                allowed_modules.add(mapped_name)
        
        # Agregar módulos base
        allowed_modules.update(base_modules & all_module_names)
        
        # Módulos a bloquear = todos los demás
        modules_to_block = all_module_names - allowed_modules
        
        # Configurar block_modules en el usuario
        user.block_modules = []
        for module_name in sorted(modules_to_block):
            user.append("block_modules", {"module": module_name})
        
        user.save(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"✓ Módulos permitidos: {len(allowed_modules)}")
        print(f"  {', '.join(sorted(allowed_modules))}")
        print(f"✓ Módulos bloqueados: {len(modules_to_block)}")
        if modules_to_block:
            print(f"  {', '.join(sorted(list(modules_to_block))[:10])}")
            if len(modules_to_block) > 10:
                print(f"  ... y {len(modules_to_block) - 10} más")
        
    except Exception as e:
        logger.warning(f"Error al configurar módulos: {str(e)}")
        print(f"⚠ No se pudo configurar módulos: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Configurar Module Profile si está habilitado (opcional, para referencia)
    if use_module_profile:
        print("\n" + "-" * 70)
        print("CONFIGURANDO MODULE PROFILE (referencia):")
        print("-" * 70)
        
        try:
            # Crear/actualizar Module Profile para este perfil
            module_profile_name = f"Module Profile - {profile_name}"
            module_profile = create_or_update_module_profile(
                profile_name=module_profile_name,
                modules=profile_config["visible_modules"],
                roles=profile_config["standard_roles"] + profile_config["custom_roles"]
            )
            print(f"✓ Module Profile '{module_profile_name}' configurado")
        except Exception as e:
            logger.warning(f"Error al configurar Module Profile: {str(e)}")
            print(f"⚠ No se pudo configurar Module Profile: {str(e)}")
    
    # Verificar permisos
    print("\n" + "-" * 70)
    print("VERIFICACIÓN DE PERMISOS:")
    print("-" * 70)
    
    # Verificar que los permisos estén configurados (usando setup_permissions)
    try:
        from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import setup_permissions_for_role
        
        for custom_role in profile_config["custom_roles"]:
            print(f"Configurando permisos para rol personalizado: {custom_role}")
            setup_permissions_for_role(custom_role, use_extended_strategy=True)
        
        frappe.db.commit()
        print("Permisos configurados exitosamente")
    except Exception as e:
        logger.warning(f"Error al configurar permisos: {str(e)}")
    
    return {
        "success": True,
        "user": user.name,
        "email": email,
        "profile": profile_name,
        "roles_added": list(roles_to_add),
        "roles_removed": list(roles_to_remove),
        "visible_modules": profile_config["visible_modules"],
        "module_profile": module_profile_name if use_module_profile else None,
    }


def list_available_profiles():
    """Lista todos los perfiles predefinidos disponibles."""
    print("=" * 70)
    print("PERFILES DE USUARIO DISPONIBLES")
    print("=" * 70)
    
    for profile_name, config in USER_PROFILES.items():
        print(f"\n{profile_name}:")
        print(f"  Descripción: {config['description']}")
        print(f"  Módulos: {', '.join(config['visible_modules'])}")
        print(f"  Roles personalizados: {', '.join(config['custom_roles'])}")
        print(f"  Roles estándar: {', '.join(config['standard_roles'])}")
    
    return list(USER_PROFILES.keys())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python setup_user_profiles.py analyze <user_email>")
        print("  python setup_user_profiles.py setup <user_email> <profile_name> [full_name]")
        print("  python setup_user_profiles.py list")
        sys.exit(1)
    
    command = sys.argv[1]
    site = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "analyze" and sys.argv[2] != "list" else "frontend"
    
    frappe.init(site=site)
    frappe.connect()
    
    if command == "analyze":
        user_email = sys.argv[2] if len(sys.argv) > 2 else None
        if not user_email:
            print("Error: Se requiere email de usuario")
            sys.exit(1)
        analyze_user_profile(user_email)
    
    elif command == "setup":
        if len(sys.argv) < 4:
            print("Error: Se requiere email y nombre de perfil")
            sys.exit(1)
        email = sys.argv[2]
        profile = sys.argv[3]
        full_name = sys.argv[4] if len(sys.argv) > 4 else None
        setup_user_from_profile(email, profile, full_name)
    
    elif command == "list":
        list_available_profiles()
    
    else:
        print(f"Comando desconocido: {command}")
        sys.exit(1)
    
    frappe.db.close()
