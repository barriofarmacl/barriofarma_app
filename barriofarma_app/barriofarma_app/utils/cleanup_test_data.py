# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Utilidad para limpiar datos de prueba residuales
Ejecutar con: bench --site [sitename] console < cleanup_test_data.py
"""

import frappe


def cleanup_test_data():
    """Limpiar todos los datos de prueba residuales"""
    frappe.set_user("Administrator")
    
    print("=== Limpiando datos de prueba residuales ===\n")
    
    # Limpiar Purchase Invoices de prueba
    # Buscar por suppliers de prueba (incluso si el supplier ya no existe)
    print("Limpiando Purchase Invoices...")
    pis = frappe.get_all("Purchase Invoice", filters={"supplier": ("like", "TEST-%")}, fields=["name", "supplier", "docstatus"])
    for pi in pis:
        try:
            pi_doc = frappe.get_doc("Purchase Invoice", pi.name)
            if pi_doc.docstatus == 1:
                pi_doc.cancel()
            frappe.delete_doc("Purchase Invoice", pi.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {pi.name} (supplier: {pi.supplier})")
        except Exception as e:
            print(f"  ✗ Error eliminando {pi.name}: {e}")
    
    # Limpiar Purchase Receipts de prueba
    # Buscar por suppliers de prueba (incluso si el supplier ya no existe)
    print("\nLimpiando Purchase Receipts...")
    prs = frappe.get_all("Purchase Receipt", filters={"supplier": ("like", "TEST-%")}, fields=["name", "supplier", "docstatus"])
    for pr in prs:
        try:
            pr_doc = frappe.get_doc("Purchase Receipt", pr.name)
            if pr_doc.docstatus == 1:
                pr_doc.cancel()
            frappe.delete_doc("Purchase Receipt", pr.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {pr.name} (supplier: {pr.supplier})")
        except Exception as e:
            print(f"  ✗ Error eliminando {pr.name}: {e}")
    
    # Limpiar Purchase Orders de prueba
    # Buscar por suppliers de prueba (incluso si el supplier ya no existe)
    print("\nLimpiando Purchase Orders...")
    pos = frappe.get_all("Purchase Order", filters={"supplier": ("like", "TEST-%")}, fields=["name", "supplier", "docstatus"])
    for po in pos:
        try:
            po_doc = frappe.get_doc("Purchase Order", po.name)
            if po_doc.docstatus == 1:
                po_doc.cancel()
            frappe.delete_doc("Purchase Order", po.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {po.name} (supplier: {po.supplier})")
        except Exception as e:
            print(f"  ✗ Error eliminando {po.name}: {e}")
    
    # Limpiar Batches de prueba
    print("\nLimpiando Batches...")
    batches = frappe.get_all("Batch", filters={"batch_id": ("like", "BATCH-%")}, fields=["name", "batch_id"])
    for batch in batches:
        try:
            frappe.delete_doc("Batch", batch.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {batch.batch_id}")
        except Exception as e:
            print(f"  ✗ Error eliminando {batch.batch_id}: {e}")
    
    # Limpiar Warehouses de prueba
    # Nota: Los warehouses pueden tener registros de inventario asociados
    # Primero limpiar Stock Ledger Entries y Bins relacionados
    print("\nLimpiando Warehouses...")
    # Buscar por nombre o por código que empiece con TEST-WH
    warehouses = frappe.db.sql("""
        SELECT name, warehouse_name 
        FROM `tabWarehouse` 
        WHERE name LIKE 'TEST-WH%' 
           OR warehouse_name LIKE 'TEST-WH%'
           OR warehouse_name LIKE 'TEST-%'
    """, as_dict=True)
    
    for wh in warehouses:
        try:
            # Primero eliminar Stock Ledger Entries relacionados
            sle_count = frappe.db.count("Stock Ledger Entry", {"warehouse": wh.name})
            if sle_count > 0:
                frappe.db.sql("DELETE FROM `tabStock Ledger Entry` WHERE warehouse = %s", (wh.name,))
                print(f"  ✓ Eliminados {sle_count} Stock Ledger Entries de {wh.warehouse_name}")
            
            # Eliminar Bins relacionados
            bin_count = frappe.db.count("Bin", {"warehouse": wh.name})
            if bin_count > 0:
                frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse = %s", (wh.name,))
                print(f"  ✓ Eliminados {bin_count} Bins de {wh.warehouse_name}")
            
            # Eliminar Shelf Movements relacionados (si existen)
            # Primero obtener los shelves del warehouse
            shelves = frappe.db.sql("SELECT name FROM `tabShelf` WHERE warehouse = %s", (wh.name,), as_dict=True)
            if shelves:
                shelf_names = [s["name"] for s in shelves]
                # Contar movimientos antes de eliminar
                shelf_movement_count = frappe.db.sql("""
                    SELECT COUNT(*) as count 
                    FROM `tabShelf Movement` 
                    WHERE shelf IN ({})
                """.format(",".join(["%s"] * len(shelf_names))), tuple(shelf_names), as_dict=True)[0]["count"]
                
                if shelf_movement_count > 0:
                    frappe.db.sql("DELETE FROM `tabShelf Movement` WHERE shelf IN ({})".format(
                        ",".join(["%s"] * len(shelf_names))
                    ), tuple(shelf_names))
                    print(f"  ✓ Eliminados {shelf_movement_count} movimientos de shelves relacionados con {wh.warehouse_name}")
            
            # Eliminar Shelves relacionados (si existen)
            shelf_count = frappe.db.count("Shelf", {"warehouse": wh.name})
            if shelf_count > 0:
                shelves = frappe.get_all("Shelf", filters={"warehouse": wh.name}, fields=["name"])
                for shelf in shelves:
                    try:
                        frappe.delete_doc("Shelf", shelf.name, force=True, ignore_permissions=True)
                    except:
                        frappe.db.sql("DELETE FROM `tabShelf` WHERE name = %s", (shelf.name,))
                print(f"  ✓ Eliminados {shelf_count} Shelves relacionados con {wh.warehouse_name}")
            
            # Eliminar Stock Entries relacionados (si existen y están en draft)
            stock_entries = frappe.get_all("Stock Entry", 
                filters={"docstatus": 0, "from_warehouse": wh.name}, 
                fields=["name"])
            stock_entries.extend(frappe.get_all("Stock Entry", 
                filters={"docstatus": 0, "to_warehouse": wh.name}, 
                fields=["name"]))
            if stock_entries:
                for se in stock_entries:
                    try:
                        frappe.delete_doc("Stock Entry", se.name, force=True, ignore_permissions=True)
                    except:
                        pass
                print(f"  ✓ Eliminados {len(stock_entries)} Stock Entries relacionados con {wh.warehouse_name}")
            
            # Ahora intentar eliminar el warehouse usando el método estándar
            try:
                frappe.delete_doc("Warehouse", wh.name, force=True, ignore_permissions=True)
                print(f"  ✓ Eliminado: {wh.warehouse_name}")
            except Exception as e:
                # Si falla, intentar directamente desde BD
                print(f"  ⚠️  Error con delete_doc, intentando eliminación directa: {e}")
                frappe.db.sql("DELETE FROM `tabWarehouse` WHERE name = %s", (wh.name,))
                print(f"  ✓ Eliminado directamente de BD: {wh.warehouse_name}")
                
        except Exception as e:
            print(f"  ✗ Error eliminando {wh.warehouse_name}: {e}")
            # Último intento: eliminación directa de BD
            try:
                frappe.db.sql("DELETE FROM `tabWarehouse` WHERE name = %s", (wh.name,))
                print(f"  ✓ Eliminado directamente de BD (último intento): {wh.warehouse_name}")
            except Exception as e2:
                print(f"  ✗ Error crítico eliminando {wh.warehouse_name}: {e2}")
    
    # Limpiar Suppliers de prueba
    print("\nLimpiando Suppliers...")
    suppliers = frappe.get_all("Supplier", filters={"supplier_name": ("like", "TEST-SUPPLIER-%")}, fields=["name", "supplier_name"])
    for supplier in suppliers:
        try:
            frappe.delete_doc("Supplier", supplier.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {supplier.supplier_name}")
        except Exception as e:
            print(f"  ✗ Error eliminando {supplier.supplier_name}: {e}")
    
    # Limpiar Items de prueba
    print("\nLimpiando Items...")
    items = frappe.get_all("Item", filters={"item_code": ("like", "TEST-ITEM-%")}, fields=["name", "item_code"])
    for item in items:
        try:
            frappe.delete_doc("Item", item.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {item.item_code}")
        except Exception as e:
            print(f"  ✗ Error eliminando {item.item_code}: {e}")
    
    # Limpiar Prescriptions de prueba
    print("\nLimpiando Prescriptions...")
    # Usar SQL directo porque los filtros OR complejos no funcionan bien con get_all
    prescriptions = frappe.db.sql("""
        SELECT name, patient_name, doctor_name, status
        FROM `tabPrescription`
        WHERE patient_name LIKE 'Paciente Test%'
           OR patient_name LIKE 'Test%'
           OR doctor_name LIKE 'Dr. Test%'
           OR doctor_name LIKE 'TEST-%'
    """, as_dict=True)
    for presc in prescriptions:
        try:
            frappe.delete_doc("Prescription", presc.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {presc.name} (patient: {presc.patient_name}, doctor: {presc.doctor_name})")
        except Exception as e:
            print(f"  ✗ Error eliminando {presc.name}: {e}")
    
    # Limpiar Prescriptions con referencias rotas (doctor que no existe)
    print("\nLimpiando Prescriptions con referencias rotas...")
    broken_prescriptions = frappe.db.sql("""
        SELECT name, doctor, doctor_name, patient_name
        FROM `tabPrescription`
        WHERE doctor NOT IN (SELECT name FROM `tabDoctor`)
          AND doctor IS NOT NULL
          AND doctor != ''
          AND (patient_name LIKE 'Paciente Test%' 
               OR patient_name LIKE 'Test%'
               OR doctor_name LIKE 'Dr. Test%'
               OR doctor_name LIKE 'TEST-%')
    """, as_dict=True)
    for presc in broken_prescriptions:
        try:
            frappe.delete_doc("Prescription", presc.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado (referencia rota): {presc.name} (doctor: {presc.doctor})")
        except Exception as e:
            print(f"  ✗ Error eliminando {presc.name}: {e}")
    
    # Limpiar Doctors de prueba
    print("\nLimpiando Doctors...")
    doctors = frappe.db.sql("""
        SELECT name, doctor_name, license_number
        FROM `tabDoctor`
        WHERE doctor_name LIKE 'Dr. Test%'
           OR doctor_name LIKE 'TEST-%'
           OR license_number LIKE 'TEST-LIC%'
    """, as_dict=True)
    for doctor in doctors:
        try:
            frappe.delete_doc("Doctor", doctor.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {doctor.doctor_name} (licencia: {doctor.license_number})")
        except Exception as e:
            print(f"  ✗ Error eliminando {doctor.doctor_name}: {e}")
    
    frappe.db.commit()
    print("\n=== Limpieza completada ===")


def check_test_data():
    """Verificar datos de prueba residuales sin eliminarlos"""
    print("=== Verificando datos de prueba residuales ===\n")
    
    # Items de prueba
    test_items = frappe.get_all("Item", filters={"item_code": ("like", "TEST-ITEM-%")}, fields=["name", "item_code", "creation"])
    print(f"Items de prueba encontrados: {len(test_items)}")
    if test_items:
        for item in test_items[:10]:
            print(f"  - {item.item_code} (creado: {item.creation})")
        if len(test_items) > 10:
            print(f"  ... y {len(test_items) - 10} más")
    
    # Suppliers de prueba
    test_suppliers = frappe.get_all("Supplier", filters={"supplier_name": ("like", "TEST-SUPPLIER-%")}, fields=["name", "supplier_name", "creation"])
    print(f"\nSuppliers de prueba encontrados: {len(test_suppliers)}")
    if test_suppliers:
        for supplier in test_suppliers[:10]:
            print(f"  - {supplier.supplier_name} (creado: {supplier.creation})")
        if len(test_suppliers) > 10:
            print(f"  ... y {len(test_suppliers) - 10} más")
    
    # Warehouses de prueba (buscar por nombre o código)
    test_warehouses = frappe.db.sql("""
        SELECT name, warehouse_name, creation 
        FROM `tabWarehouse` 
        WHERE name LIKE 'TEST-WH%' 
           OR warehouse_name LIKE 'TEST-WH%'
           OR warehouse_name LIKE 'TEST-%'
    """, as_dict=True)
    print(f"\nWarehouses de prueba encontrados: {len(test_warehouses)}")
    if test_warehouses:
        for wh in test_warehouses[:10]:
            print(f"  - {wh.warehouse_name} ({wh.name}, creado: {wh.creation})")
        if len(test_warehouses) > 10:
            print(f"  ... y {len(test_warehouses) - 10} más")
    
    # Batches de prueba
    test_batches = frappe.get_all("Batch", filters={"batch_id": ("like", "BATCH-%")}, fields=["name", "batch_id", "creation"])
    print(f"\nBatches de prueba encontrados: {len(test_batches)}")
    if test_batches:
        for batch in test_batches[:10]:
            print(f"  - {batch.batch_id} (creado: {batch.creation})")
        if len(test_batches) > 10:
            print(f"  ... y {len(test_batches) - 10} más")
    
    # Purchase Orders de prueba (buscar por suppliers de prueba, incluso si el supplier ya no existe)
    test_pos = frappe.get_all("Purchase Order", filters={"supplier": ("like", "TEST-%")}, fields=["name", "supplier", "creation"])
    print(f"\nPurchase Orders de prueba encontrados: {len(test_pos)}")
    if test_pos:
        for po in test_pos[:10]:
            print(f"  - {po.name} (supplier: {po.supplier}, creado: {po.creation})")
        if len(test_pos) > 10:
            print(f"  ... y {len(test_pos) - 10} más")
    
    # Purchase Receipts de prueba (buscar por suppliers de prueba, incluso si el supplier ya no existe)
    test_prs = frappe.get_all("Purchase Receipt", filters={"supplier": ("like", "TEST-%")}, fields=["name", "supplier", "creation"])
    print(f"\nPurchase Receipts de prueba encontrados: {len(test_prs)}")
    if test_prs:
        for pr in test_prs[:10]:
            print(f"  - {pr.name} (supplier: {pr.supplier}, creado: {pr.creation})")
        if len(test_prs) > 10:
            print(f"  ... y {len(test_prs) - 10} más")
    
    # Purchase Invoices de prueba (buscar por suppliers de prueba, incluso si el supplier ya no existe)
    test_pis = frappe.get_all("Purchase Invoice", filters={"supplier": ("like", "TEST-%")}, fields=["name", "supplier", "creation"])
    print(f"\nPurchase Invoices de prueba encontrados: {len(test_pis)}")
    if test_pis:
        for pi in test_pis[:10]:
            print(f"  - {pi.name} (supplier: {pi.supplier}, creado: {pi.creation})")
        if len(test_pis) > 10:
            print(f"  ... y {len(test_pis) - 10} más")
    
    # Prescriptions de prueba
    test_prescriptions = frappe.db.sql("""
        SELECT name, patient_name, doctor_name, creation
        FROM `tabPrescription`
        WHERE patient_name LIKE 'Paciente Test%'
           OR patient_name LIKE 'Test%'
           OR doctor_name LIKE 'Dr. Test%'
           OR doctor_name LIKE 'TEST-%'
    """, as_dict=True)
    print(f"\nPrescriptions de prueba encontradas: {len(test_prescriptions)}")
    if test_prescriptions:
        for presc in test_prescriptions[:10]:
            print(f"  - {presc.name} (patient: {presc.patient_name}, doctor: {presc.doctor_name}, creado: {presc.creation})")
        if len(test_prescriptions) > 10:
            print(f"  ... y {len(test_prescriptions) - 10} más")
    
    # Prescriptions con referencias rotas
    broken_prescriptions = frappe.db.sql("""
        SELECT name, doctor, doctor_name, patient_name, creation
        FROM `tabPrescription`
        WHERE doctor NOT IN (SELECT name FROM `tabDoctor`)
          AND doctor IS NOT NULL
          AND doctor != ''
    """, as_dict=True)
    print(f"\nPrescriptions con referencias rotas (doctor no existe): {len(broken_prescriptions)}")
    if broken_prescriptions:
        for presc in broken_prescriptions[:10]:
            print(f"  - {presc.name} (doctor: {presc.doctor}, patient: {presc.patient_name}, creado: {presc.creation})")
        if len(broken_prescriptions) > 10:
            print(f"  ... y {len(broken_prescriptions) - 10} más")
    
    # Doctors de prueba
    test_doctors = frappe.db.sql("""
        SELECT name, doctor_name, license_number, creation
        FROM `tabDoctor`
        WHERE doctor_name LIKE 'Dr. Test%'
           OR doctor_name LIKE 'TEST-%'
           OR license_number LIKE 'TEST-LIC%'
    """, as_dict=True)
    print(f"\nDoctors de prueba encontrados: {len(test_doctors)}")
    if test_doctors:
        for doctor in test_doctors[:10]:
            print(f"  - {doctor.doctor_name} (licencia: {doctor.license_number}, creado: {doctor.creation})")
        if len(test_doctors) > 10:
            print(f"  ... y {len(test_doctors) - 10} más")
    
    print("\n=== Resumen ===")
    print(f"Total Items: {len(test_items)}")
    print(f"Total Suppliers: {len(test_suppliers)}")
    print(f"Total Warehouses: {len(test_warehouses)}")
    print(f"Total Batches: {len(test_batches)}")
    print(f"Total Purchase Orders: {len(test_pos)}")
    print(f"Total Purchase Receipts: {len(test_prs)}")
    print(f"Total Purchase Invoices: {len(test_pis)}")
    print(f"Total Prescriptions: {len(test_prescriptions)}")
    print(f"Total Prescriptions con referencias rotas: {len(broken_prescriptions)}")
    print(f"Total Doctors: {len(test_doctors)}")


# =============================================================================
# LIMPIEZA DE USUARIOS DE PRUEBA
# =============================================================================

# Usuarios protegidos que NO deben eliminarse
PROTECTED_USERS = [
    "Administrator",
    "Guest",
    "administrator",
    "guest"
]


def cleanup_test_users():
    """
    Elimina TODOS los usuarios de prueba, incluyendo:
    - Usuarios de Frappe Framework (_Test*)
    - Usuarios de BarrioFarma (test_*)
    - Usuarios con emails @example.com
    
    Uso:
        bench --site barriofarma.localhost execute \
            barriofarma_app.barriofarma_app.utils.cleanup_test_data.cleanup_test_users
    """
    frappe.set_user("Administrator")
    
    print("\n" + "=" * 70)
    print("LIMPIEZA DE USUARIOS DE PRUEBA")
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
    print("RESUMEN USUARIOS")
    print("-" * 70)
    
    if deleted:
        print(f"\nEliminados ({len(deleted)}):")
        for u in deleted:
            print(f"  - {u}")
    else:
        print("\nNo se eliminaron usuarios.")
    
    if skipped:
        print(f"\nOmitidos ({len(skipped)}):")
        for u in skipped:
            print(f"  - {u}")
    
    if errors:
        print(f"\nErrores ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    
    print("=" * 70)
    
    frappe.db.commit()
    return {"deleted": deleted, "skipped": skipped, "errors": errors}


def check_test_users():
    """
    Lista todos los usuarios de prueba sin eliminarlos.
    
    Uso:
        bench --site barriofarma.localhost execute \
            barriofarma_app.barriofarma_app.utils.cleanup_test_data.check_test_users
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
    
    # 3. Usuarios con email @example.com (excluyendo los ya listados)
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


def cleanup_all():
    """
    Ejecuta limpieza completa: datos de prueba + usuarios de prueba.
    
    Uso:
        bench --site barriofarma.localhost execute \
            barriofarma_app.barriofarma_app.utils.cleanup_test_data.cleanup_all
    """
    print("\n" + "=" * 70)
    print("LIMPIEZA COMPLETA DEL SISTEMA")
    print("=" * 70)
    
    # 1. Limpiar datos de prueba
    cleanup_test_data()
    
    # 2. Limpiar usuarios de prueba
    cleanup_test_users()
    
    print("\n" + "=" * 70)
    print("LIMPIEZA COMPLETA FINALIZADA")
    print("=" * 70)


if __name__ == "__main__":
    # Ejecutar verificación primero
    check_test_data()
    check_test_users()
    
    # Preguntar si quiere limpiar
    print("\n¿Desea limpiar estos datos? (s/n): ", end="")
    # En modo interactivo, el usuario puede responder
    # Para ejecución automática, descomentar la siguiente línea:
    # cleanup_all()
