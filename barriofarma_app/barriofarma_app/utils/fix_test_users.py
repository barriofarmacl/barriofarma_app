# -*- coding: utf-8 -*-
"""
Script temporal para actualizar usuarios de prueba existentes
que fueron creados con email como name
"""
import frappe

# Mapeo de usuarios y sus roles
USER_ROLES = {
    "test_admin@barriofarma.cl": ["System Manager"],
    "test_stock_manager@barriofarma.cl": ["Stock Manager", "Item Manager", "Stock User"],
    "test_bodega@barriofarma.cl": ["Stock User"],
    "test_farmaceutico@barriofarma.cl": ["Stock Manager", "Stock User"],
    "test_comprador@barriofarma.cl": ["Purchase Manager", "Purchase User"],
    "test_vendedor@barriofarma.cl": ["Sales User"],
    "test_cajero@barriofarma.cl": ["Sales User", "Accounts User"]
}

def fix_test_users():
    """Actualiza los roles de los usuarios de prueba existentes."""
    updated = []
    errors = []
    
    for user_email, roles in USER_ROLES.items():
        try:
            if frappe.db.exists("User", user_email):
                user = frappe.get_doc("User", user_email)
                existing_roles = [r.role for r in user.roles]
                
                # Agregar roles faltantes
                for role in roles:
                    if role not in existing_roles:
                        if frappe.db.exists("Role", role):
                            user.append("roles", {"role": role})
                        else:
                            print(f"  ADVERTENCIA: Rol '{role}' no existe")
                
                user.save(ignore_permissions=True)
                updated.append(user_email)
                print(f"Usuario actualizado: {user_email}")
            else:
                print(f"Usuario no encontrado: {user_email}")
        except Exception as e:
            errors.append(f"{user_email}: {str(e)}")
            print(f"Error actualizando {user_email}: {str(e)}")
    
    frappe.db.commit()
    
    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)
    print(f"Usuarios actualizados: {len(updated)}")
    if errors:
        print(f"Errores: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
    print("=" * 50)
    
    return {"updated": updated, "errors": errors}

