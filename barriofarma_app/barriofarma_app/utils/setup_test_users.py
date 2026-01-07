# -*- coding: utf-8 -*-
"""
Setup de usuarios de prueba para tests UI (Cypress)

Uso:
    bench --site barriofarma.localhost execute \
        barriofarma_app.barriofarma_app.utils.setup_test_users.create_test_users

Para limpiar:
    bench --site barriofarma.localhost execute \
        barriofarma_app.barriofarma_app.utils.setup_test_users.delete_test_users
"""
import frappe
from frappe import _


# Configuracion de usuarios de prueba
TEST_USERS = [
    {
        "name": "test_admin",
        "email": "test_admin@barriofarma.cl",
        "first_name": "Admin",
        "last_name": "Test",
        "roles": ["System Manager"],
        "description": "Administrador del sistema para tests"
    },
    {
        "name": "test_stock_manager",
        "email": "test_stock_manager@barriofarma.cl",
        "first_name": "Jefe",
        "last_name": "Inventario",
        "roles": ["Stock Manager", "Item Manager", "Stock User"],
        "description": "Jefe de inventario - gestion completa de stock y productos"
    },
    {
        "name": "test_bodega",
        "email": "test_bodega@barriofarma.cl",
        "first_name": "Auxiliar",
        "last_name": "Bodega",
        "roles": ["Stock User"],
        "description": "Auxiliar de bodega - recepciones y transferencias"
    },
    {
        "name": "test_farmaceutico",
        "email": "test_farmaceutico@barriofarma.cl",
        "first_name": "Quimico",
        "last_name": "Farmaceutico",
        "roles": ["Stock Manager", "Stock User"],
        "description": "Farmaceutico - control de calidad en recepciones"
    },
    {
        "name": "test_comprador",
        "email": "test_comprador@barriofarma.cl",
        "first_name": "Comprador",
        "last_name": "Farmacia",
        "roles": ["Purchase Manager", "Purchase User"],
        "description": "Comprador - gestion de ordenes de compra"
    },
    {
        "name": "test_vendedor",
        "email": "test_vendedor@barriofarma.cl",
        "first_name": "Vendedor",
        "last_name": "Farmacia",
        "roles": ["Sales User"],
        "description": "Vendedor - ventas desde formularios"
    },
    {
        "name": "test_cajero",
        "email": "test_cajero@barriofarma.cl",
        "first_name": "Cajero",
        "last_name": "POS",
        "roles": ["Sales User", "Accounts User"],
        "description": "Cajero - operacion de Point of Sale"
    }
]

DEFAULT_PASSWORD = "Test@123"


def create_test_users():
    """Crea todos los usuarios de prueba con sus roles asignados."""
    created = []
    updated = []
    errors = []
    
    for user_config in TEST_USERS:
        try:
            result = create_or_update_user(user_config)
            if result == "created":
                created.append(user_config["name"])
            elif result == "updated":
                updated.append(user_config["name"])
        except Exception as e:
            errors.append(f"{user_config['name']}: {str(e)}")
    
    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN DE CREACION DE USUARIOS DE PRUEBA")
    print("=" * 50)
    
    if created:
        print(f"\nUsuarios creados ({len(created)}):")
        for u in created:
            print(f"  - {u}")
    
    if updated:
        print(f"\nUsuarios actualizados ({len(updated)}):")
        for u in updated:
            print(f"  - {u}")
    
    if errors:
        print(f"\nErrores ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    
    print(f"\nPassword por defecto: {DEFAULT_PASSWORD}")
    print("=" * 50)
    
    frappe.db.commit()
    return {"created": created, "updated": updated, "errors": errors}


def create_or_update_user(user_config):
    """Crea o actualiza un usuario de prueba."""
    user_name = user_config["name"]
    
    if frappe.db.exists("User", user_name):
        # Actualizar usuario existente
        user = frappe.get_doc("User", user_name)
        user.first_name = user_config["first_name"]
        user.last_name = user_config["last_name"]
        user.enabled = 1
        
        # Actualizar roles
        update_user_roles(user, user_config["roles"])
        
        user.save(ignore_permissions=True)
        print(f"Usuario actualizado: {user_name}")
        return "updated"
    else:
        # Crear nuevo usuario
        user = frappe.get_doc({
            "doctype": "User",
            "name": user_name,
            "email": user_config["email"],
            "first_name": user_config["first_name"],
            "last_name": user_config["last_name"],
            "enabled": 1,
            "user_type": "System User",
            "send_welcome_email": 0,
            "new_password": DEFAULT_PASSWORD
        })
        user.insert(ignore_permissions=True)
        
        # Asignar roles
        update_user_roles(user, user_config["roles"])
        user.save(ignore_permissions=True)
        
        print(f"Usuario creado: {user_name}")
        return "created"


def update_user_roles(user, roles):
    """Actualiza los roles de un usuario."""
    # Limpiar roles existentes (excepto los del sistema)
    existing_roles = [r.role for r in user.roles]
    
    for role_name in roles:
        if role_name not in existing_roles:
            # Verificar que el rol existe
            if frappe.db.exists("Role", role_name):
                user.append("roles", {"role": role_name})
            else:
                print(f"  ADVERTENCIA: Rol '{role_name}' no existe en el sistema")


def delete_test_users():
    """Elimina todos los usuarios de prueba."""
    deleted = []
    errors = []
    
    for user_config in TEST_USERS:
        user_name = user_config["name"]
        try:
            if frappe.db.exists("User", user_name):
                frappe.delete_doc("User", user_name, force=True)
                deleted.append(user_name)
                print(f"Usuario eliminado: {user_name}")
        except Exception as e:
            errors.append(f"{user_name}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("RESUMEN DE ELIMINACION DE USUARIOS DE PRUEBA")
    print("=" * 50)
    
    if deleted:
        print(f"\nUsuarios eliminados ({len(deleted)}):")
        for u in deleted:
            print(f"  - {u}")
    
    if errors:
        print(f"\nErrores ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    
    print("=" * 50)
    
    frappe.db.commit()
    return {"deleted": deleted, "errors": errors}


def setup_pos_profile_for_cajero():
    """
    Configura el POS Profile para el usuario test_cajero.
    Debe ejecutarse despues de crear los usuarios.
    
    Uso:
        bench --site barriofarma.localhost execute \
            barriofarma_app.barriofarma_app.utils.setup_test_users.setup_pos_profile_for_cajero
    """
    # Buscar POS Profile existente o crear uno
    pos_profile_name = "Cajero BarrioFarma Test"
    
    if not frappe.db.exists("POS Profile", pos_profile_name):
        print(f"POS Profile '{pos_profile_name}' no existe.")
        print("Creando POS Profile basico...")
        
        # Obtener warehouse y company por defecto
        company = frappe.defaults.get_global_default("company")
        if not company:
            companies = frappe.get_all("Company", limit=1)
            if companies:
                company = companies[0].name
            else:
                print("ERROR: No hay Company configurada en el sistema")
                return
        
        # Obtener warehouse
        warehouse = frappe.db.get_value("Warehouse", 
            {"company": company, "is_group": 0}, "name")
        if not warehouse:
            warehouses = frappe.get_all("Warehouse", 
                filters={"is_group": 0}, limit=1)
            if warehouses:
                warehouse = warehouses[0].name
            else:
                print("ERROR: No hay Warehouse configurado en el sistema")
                return
        
        # Obtener Price List
        price_list = frappe.db.get_value("Price List", 
            {"selling": 1, "enabled": 1}, "name")
        if not price_list:
            price_list = "Standard Selling"
        
        # Crear POS Profile
        pos_profile = frappe.get_doc({
            "doctype": "POS Profile",
            "name": pos_profile_name,
            "company": company,
            "warehouse": warehouse,
            "selling_price_list": price_list,
            "currency": frappe.db.get_value("Company", company, "default_currency") or "CLP",
            "write_off_account": frappe.db.get_value("Account", 
                {"company": company, "account_type": "Expense Account"}, "name"),
            "write_off_cost_center": frappe.db.get_value("Cost Center", 
                {"company": company, "is_group": 0}, "name"),
        })
        
        # Agregar usuario test_cajero
        pos_profile.append("applicable_for_users", {
            "user": "test_cajero@barriofarma.cl",
            "default": 1
        })
        
        try:
            pos_profile.insert(ignore_permissions=True)
            print(f"POS Profile creado: {pos_profile_name}")
        except Exception as e:
            print(f"ERROR creando POS Profile: {str(e)}")
            return
    else:
        # Actualizar POS Profile existente
        pos_profile = frappe.get_doc("POS Profile", pos_profile_name)
        
        # Verificar si test_cajero ya esta asignado
        users = [u.user for u in pos_profile.applicable_for_users]
        if "test_cajero@barriofarma.cl" not in users:
            pos_profile.append("applicable_for_users", {
                "user": "test_cajero@barriofarma.cl",
                "default": 1
            })
            pos_profile.save(ignore_permissions=True)
            print(f"Usuario test_cajero@barriofarma.cl agregado a POS Profile: {pos_profile_name}")
        else:
            print(f"Usuario test_cajero@barriofarma.cl ya esta en POS Profile: {pos_profile_name}")
    
    frappe.db.commit()


def get_test_users_status():
    """
    Muestra el estado de los usuarios de prueba.
    
    Uso:
        bench --site barriofarma.localhost execute \
            barriofarma_app.barriofarma_app.utils.setup_test_users.get_test_users_status
    """
    print("\n" + "=" * 70)
    print("ESTADO DE USUARIOS DE PRUEBA")
    print("=" * 70)
    
    for user_config in TEST_USERS:
        user_name = user_config["name"]
        exists = frappe.db.exists("User", user_name)
        
        if exists:
            user = frappe.get_doc("User", user_name)
            roles = [r.role for r in user.roles]
            status = "ACTIVO" if user.enabled else "DESHABILITADO"
            print(f"\n{user_name}: {status}")
            print(f"  Email: {user.email}")
            print(f"  Roles: {', '.join(roles)}")
        else:
            print(f"\n{user_name}: NO EXISTE")
    
    print("\n" + "=" * 70)


# =============================================================================
# LIMPIEZA DE USUARIOS DE PRUEBA DE FRAPPE FRAMEWORK
# =============================================================================

# Usuarios protegidos que NO deben eliminarse
PROTECTED_USERS = [
    "Administrator",
    "Guest",
    "administrator",
    "guest"
]


def cleanup_all_test_users():
    """
    Elimina TODOS los usuarios de prueba, incluyendo:
    - Usuarios de BarrioFarma (test_*)
    - Usuarios de Frappe Framework (_Test*)
    - Usuarios con emails @example.com
    
    Uso:
        bench --site barriofarma.localhost execute \
            barriofarma_app.barriofarma_app.utils.setup_test_users.cleanup_all_test_users
    """
    print("\n" + "=" * 70)
    print("LIMPIEZA COMPLETA DE USUARIOS DE PRUEBA")
    print("=" * 70)
    
    deleted = []
    errors = []
    skipped = []
    
    # 1. Buscar usuarios con prefijo _Test (Frappe Framework)
    frappe_test_users = frappe.get_all("User", 
        filters=[["name", "like", "_Test%"]],
        fields=["name", "email", "full_name"]
    )
    
    # 2. Buscar usuarios con prefijo test_ (BarrioFarma)
    barriofarma_test_users = frappe.get_all("User",
        filters=[["name", "like", "test_%"]],
        fields=["name", "email", "full_name"]
    )
    
    # 3. Buscar usuarios con email @example.com (usuarios de prueba genericos)
    example_email_users = frappe.get_all("User",
        filters=[["email", "like", "%@example.com"]],
        fields=["name", "email", "full_name"]
    )
    
    # Combinar y eliminar duplicados
    all_test_users = {}
    for user in frappe_test_users + barriofarma_test_users + example_email_users:
        if user.name not in all_test_users:
            all_test_users[user.name] = user
    
    print(f"\nUsuarios de prueba encontrados: {len(all_test_users)}")
    
    # Eliminar cada usuario
    for user_name, user_info in all_test_users.items():
        # Verificar si es usuario protegido
        if user_name in PROTECTED_USERS:
            skipped.append(f"{user_name} (protegido)")
            continue
        
        try:
            frappe.delete_doc("User", user_name, force=True, ignore_permissions=True)
            deleted.append(f"{user_name} ({user_info.email})")
            print(f"  Eliminado: {user_name} ({user_info.email})")
        except Exception as e:
            errors.append(f"{user_name}: {str(e)}")
            print(f"  Error: {user_name} - {str(e)}")
    
    # Resumen
    print("\n" + "-" * 70)
    print("RESUMEN")
    print("-" * 70)
    
    print(f"\nEliminados ({len(deleted)}):")
    for u in deleted:
        print(f"  - {u}")
    
    if skipped:
        print(f"\nOmitidos ({len(skipped)}):")
        for u in skipped:
            print(f"  - {u}")
    
    if errors:
        print(f"\nErrores ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    
    print("\n" + "=" * 70)
    
    frappe.db.commit()
    return {"deleted": deleted, "skipped": skipped, "errors": errors}


def list_all_test_users():
    """
    Lista todos los usuarios de prueba sin eliminarlos.
    
    Uso:
        bench --site barriofarma.localhost execute \
            barriofarma_app.barriofarma_app.utils.setup_test_users.list_all_test_users
    """
    print("\n" + "=" * 70)
    print("USUARIOS DE PRUEBA EN EL SISTEMA")
    print("=" * 70)
    
    # 1. Usuarios _Test (Frappe Framework)
    frappe_test_users = frappe.get_all("User", 
        filters=[["name", "like", "_Test%"]],
        fields=["name", "email", "user_type", "enabled"],
        order_by="name"
    )
    
    print(f"\n1. Usuarios Frappe Framework (_Test*): {len(frappe_test_users)}")
    for user in frappe_test_users:
        status = "activo" if user.enabled else "deshabilitado"
        print(f"   - {user.name} ({user.email}) [{user.user_type}] - {status}")
    
    # 2. Usuarios test_ (BarrioFarma)
    barriofarma_test_users = frappe.get_all("User",
        filters=[["name", "like", "test_%"]],
        fields=["name", "email", "user_type", "enabled"],
        order_by="name"
    )
    
    print(f"\n2. Usuarios BarrioFarma (test_*): {len(barriofarma_test_users)}")
    for user in barriofarma_test_users:
        status = "activo" if user.enabled else "deshabilitado"
        print(f"   - {user.name} ({user.email}) [{user.user_type}] - {status}")
    
    # 3. Usuarios con email @example.com
    example_email_users = frappe.get_all("User",
        filters=[
            ["email", "like", "%@example.com"],
            ["name", "not like", "_Test%"],
            ["name", "not like", "test_%"]
        ],
        fields=["name", "email", "user_type", "enabled"],
        order_by="name"
    )
    
    print(f"\n3. Otros usuarios @example.com: {len(example_email_users)}")
    for user in example_email_users:
        status = "activo" if user.enabled else "deshabilitado"
        print(f"   - {user.name} ({user.email}) [{user.user_type}] - {status}")
    
    total = len(frappe_test_users) + len(barriofarma_test_users) + len(example_email_users)
    print(f"\n" + "-" * 70)
    print(f"TOTAL: {total} usuarios de prueba")
    print("=" * 70)
    
    return {
        "frappe_test": len(frappe_test_users),
        "barriofarma_test": len(barriofarma_test_users),
        "example_email": len(example_email_users),
        "total": total
    }

