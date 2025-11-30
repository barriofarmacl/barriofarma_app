# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Script de verificación para validar que no hayamos generado datos basura durante desarrollo y pruebas
"""

import frappe


def check_test_items():
    """
    Verifica si existen items de prueba en la base de datos
    Retorna lista de items encontrados
    """
    test_items = frappe.db.sql("""
        SELECT name, item_code, item_name, custom_dispensing_type, custom_control_level, 
               has_batch_no, has_expiry_date, custom_prescription_storage_required,
               custom_sanitary_registration, creation
        FROM `tabItem`
        WHERE item_code LIKE 'TEST-%'
        ORDER BY creation DESC
    """, as_dict=True)
    
    return test_items


def check_incomplete_items():
    """
    Verifica items con campos custom pero sin dispensing_type (datos inconsistentes)
    """
    incomplete_items = frappe.db.sql("""
        SELECT name, item_code, item_name, custom_dispensing_type,
               custom_control_level, custom_requires_prescription_retention,
               custom_prescription_storage_required, custom_sanitary_registration
        FROM `tabItem`
        WHERE (custom_dispensing_type IS NULL OR custom_dispensing_type = '')
        AND (
            custom_control_level IS NOT NULL OR
            custom_requires_prescription_retention IS NOT NULL OR
            custom_prescription_storage_required IS NOT NULL OR
            custom_sanitary_registration IS NOT NULL OR
            custom_active_principle IS NOT NULL OR
            custom_concentration IS NOT NULL
        )
        LIMIT 20
    """, as_dict=True)
    
    return incomplete_items


def check_validation_errors():
    """
    Verifica items que podrían tener errores de validación (violación de invariantes)
    """
    validation_errors = []
    
    # Items con Receta Retenida pero sin batch_no
    items_no_batch = frappe.db.sql("""
        SELECT name, item_code, item_name, custom_dispensing_type, has_batch_no
        FROM `tabItem`
        WHERE custom_dispensing_type = 'Venta con Receta Retenida'
        AND has_batch_no = 0
    """, as_dict=True)
    
    if items_no_batch:
        validation_errors.append({
            'tipo': 'Receta Retenida sin batch_no',
            'items': items_no_batch
        })
    
    # Items con Receta Retenida pero sin sanitary_registration
    items_no_reg = frappe.db.sql("""
        SELECT name, item_code, item_name, custom_dispensing_type, custom_sanitary_registration
        FROM `tabItem`
        WHERE custom_dispensing_type = 'Venta con Receta Retenida'
        AND (custom_sanitary_registration IS NULL OR custom_sanitary_registration = '')
    """, as_dict=True)
    
    if items_no_reg:
        validation_errors.append({
            'tipo': 'Receta Retenida sin registro sanitario',
            'items': items_no_reg
        })
    
    # Items con control_level pero sin requisitos
    items_control_incomplete = frappe.db.sql("""
        SELECT name, item_code, item_name, custom_control_level, 
               has_batch_no, has_expiry_date, custom_requires_prescription_retention
        FROM `tabItem`
        WHERE custom_control_level IN ('Psicotrópico', 'Estupefaciente')
        AND (
            has_batch_no = 0 OR
            has_expiry_date = 0 OR
            custom_requires_prescription_retention = 0
        )
    """, as_dict=True)
    
    if items_control_incomplete:
        validation_errors.append({
            'tipo': 'Control level sin requisitos completos',
            'items': items_control_incomplete
        })
    
    return validation_errors


def check_test_prescriptions():
    """
    Verifica si existen recetas de prueba en la base de datos
    Retorna lista de recetas encontradas
    """
    test_prescriptions = frappe.db.sql("""
        SELECT name, patient_name, doctor_name, status, doctor_license, creation
        FROM `tabPrescription`
        WHERE patient_name LIKE 'Paciente Test%'
           OR patient_name LIKE '%Test%'
           OR doctor_name LIKE 'Dr. Test%'
           OR doctor_license LIKE 'TEST-LIC%'
        ORDER BY creation DESC
    """, as_dict=True)
    
    return test_prescriptions


def check_test_companies():
    """
    Verifica si existen companies de prueba en la base de datos
    Retorna lista de companies encontradas (excepto Barriofarma que es la real)
    """
    test_companies = frappe.db.sql("""
        SELECT name, abbr, default_currency, country, creation
        FROM `tabCompany`
        WHERE (name LIKE '_Test%' OR name LIKE 'TEST-%' OR name LIKE '%Test Company%')
          AND name != 'Barriofarma'
        ORDER BY creation DESC
    """, as_dict=True)
    
    return test_companies


def check_test_warehouses():
    """
    Verifica si existen warehouses de prueba en la base de datos
    Retorna lista de warehouses encontrados
    """
    test_warehouses = frappe.db.sql("""
        SELECT name, warehouse_name, company, creation
        FROM `tabWarehouse`
        WHERE name LIKE 'TEST-WH%' OR warehouse_name LIKE 'TEST-%'
        ORDER BY creation DESC
    """, as_dict=True)
    
    return test_warehouses


def check_test_suppliers():
    """
    Verifica si existen suppliers de prueba en la base de datos
    Retorna lista de suppliers encontrados
    """
    test_suppliers = frappe.db.sql("""
        SELECT name, supplier_name, supplier_type, creation
        FROM `tabSupplier`
        WHERE supplier_name LIKE 'TEST-SUPPLIER%' OR name LIKE 'TEST-%'
        ORDER BY creation DESC
    """, as_dict=True)
    
    return test_suppliers


def check_test_patients():
    """
    Verifica si existen patients de prueba en la base de datos
    Retorna lista de patients encontrados
    """
    test_patients = frappe.db.sql("""
        SELECT name, patient_name, rut_dni, creation
        FROM `tabPatient`
        WHERE patient_name LIKE '%Test%' OR rut_dni LIKE 'TEST-%'
        ORDER BY creation DESC
    """, as_dict=True)
    
    return test_patients


def check_test_doctors():
    """
    Verifica si existen doctors de prueba en la base de datos
    Retorna lista de doctors encontrados
    """
    test_doctors = frappe.db.sql("""
        SELECT name, doctor_name, license_number, creation
        FROM `tabDoctor`
        WHERE doctor_name LIKE '%Test%' OR license_number LIKE 'TEST-LIC%'
        ORDER BY creation DESC
    """, as_dict=True)
    
    return test_doctors


def check_test_shelves():
    """
    Verifica si existen shelves de prueba en la base de datos
    Retorna lista de shelves encontrados
    """
    test_shelves = frappe.db.sql("""
        SELECT name, shelf_name, warehouse, creation
        FROM `tabShelf`
        WHERE shelf_name LIKE '%Test%' 
           OR name LIKE 'TEST-%' 
           OR name LIKE 'SHELF-%'
           OR shelf_name LIKE 'Estante Sin%'
        ORDER BY creation DESC
    """, as_dict=True)
    
    return test_shelves


def print_validation_report():
    """
    Imprime un reporte completo de validación
    """
    print("\n" + "="*70)
    print("REPORTE DE VALIDACIÓN DE DATOS - BarrioFarma")
    print("="*70)
    
    # 1. Items de prueba
    test_items = check_test_items()
    print(f"\n1. Items de Prueba (TEST-*): {len(test_items)}")
    if test_items:
        print("   ⚠️  ENCONTRADOS:")
        for item in test_items[:10]:  # Mostrar solo los primeros 10
            print(f"      - {item.item_code}: {item.item_name} (creado: {item.creation})")
        if len(test_items) > 10:
            print(f"      ... y {len(test_items) - 10} más")
    else:
        print("   ✅ No se encontraron items de prueba")
    
    # 2. Recetas de prueba
    test_prescriptions = check_test_prescriptions()
    print(f"\n2. Recetas de Prueba: {len(test_prescriptions)}")
    if test_prescriptions:
        print("   ⚠️  ENCONTRADAS:")
        for prescription in test_prescriptions[:10]:  # Mostrar solo las primeras 10
            print(f"      - {prescription.name}: {prescription.patient_name} - {prescription.doctor_name} ({prescription.status})")
        if len(test_prescriptions) > 10:
            print(f"      ... y {len(test_prescriptions) - 10} más")
    else:
        print("   ✅ No se encontraron recetas de prueba")
    
    # 3. Companies de prueba
    test_companies = check_test_companies()
    print(f"\n3. Companies de Prueba (_Test*, TEST-*): {len(test_companies)}")
    if test_companies:
        print("   ⚠️  ENCONTRADAS:")
        for company in test_companies[:10]:
            print(f"      - {company.name} ({company.abbr}): {company.default_currency} - {company.country}")
        if len(test_companies) > 10:
            print(f"      ... y {len(test_companies) - 10} más")
    else:
        print("   ✅ No se encontraron companies de prueba")
    
    # 4. Warehouses de prueba
    test_warehouses = check_test_warehouses()
    print(f"\n4. Warehouses de Prueba (TEST-WH*): {len(test_warehouses)}")
    if test_warehouses:
        print("   ⚠️  ENCONTRADOS:")
        for warehouse in test_warehouses[:10]:
            print(f"      - {warehouse.name}: {warehouse.company}")
        if len(test_warehouses) > 10:
            print(f"      ... y {len(test_warehouses) - 10} más")
    else:
        print("   ✅ No se encontraron warehouses de prueba")
    
    # 5. Suppliers de prueba
    test_suppliers = check_test_suppliers()
    print(f"\n5. Suppliers de Prueba (TEST-SUPPLIER*): {len(test_suppliers)}")
    if test_suppliers:
        print("   ⚠️  ENCONTRADOS:")
        for supplier in test_suppliers[:10]:
            print(f"      - {supplier.name}: {supplier.supplier_name}")
        if len(test_suppliers) > 10:
            print(f"      ... y {len(test_suppliers) - 10} más")
    else:
        print("   ✅ No se encontraron suppliers de prueba")
    
    # 6. Patients de prueba
    test_patients = check_test_patients()
    print(f"\n6. Patients de Prueba: {len(test_patients)}")
    if test_patients:
        print("   ⚠️  ENCONTRADOS:")
        for patient in test_patients[:10]:
            print(f"      - {patient.name}: {patient.patient_name} ({patient.rut_dni})")
        if len(test_patients) > 10:
            print(f"      ... y {len(test_patients) - 10} más")
    else:
        print("   ✅ No se encontraron patients de prueba")
    
    # 7. Doctors de prueba
    test_doctors = check_test_doctors()
    print(f"\n7. Doctors de Prueba: {len(test_doctors)}")
    if test_doctors:
        print("   ⚠️  ENCONTRADOS:")
        for doctor in test_doctors[:10]:
            print(f"      - {doctor.name}: {doctor.doctor_name} ({doctor.license_number})")
        if len(test_doctors) > 10:
            print(f"      ... y {len(test_doctors) - 10} más")
    else:
        print("   ✅ No se encontraron doctors de prueba")
    
    # 8. Shelves de prueba
    test_shelves = check_test_shelves()
    print(f"\n8. Shelves de Prueba (SHELF-*, Estante Sin*): {len(test_shelves)}")
    if test_shelves:
        print("   ⚠️  ENCONTRADOS:")
        for shelf in test_shelves[:10]:
            print(f"      - {shelf.name}: {shelf.shelf_name} ({shelf.warehouse}) - creado: {shelf.creation}")
        if len(test_shelves) > 10:
            print(f"      ... y {len(test_shelves) - 10} más")
    else:
        print("   ✅ No se encontraron shelves de prueba")
    
    # 9. Items incompletos
    incomplete_items = check_incomplete_items()
    print(f"\n9. Items con Campos Custom Incompletos: {len(incomplete_items)}")
    if incomplete_items:
        print("   ⚠️  ENCONTRADOS:")
        for item in incomplete_items[:10]:
            print(f"      - {item.item_code}: {item.item_name}")
            if item.custom_control_level:
                print(f"        Control: {item.custom_control_level}")
            if item.custom_sanitary_registration:
                print(f"        Reg. Sanitario: {item.custom_sanitary_registration}")
    else:
        print("   ✅ No se encontraron items incompletos")
    
    # 10. Errores de validación
    validation_errors = check_validation_errors()
    print(f"\n10. Errores de Validación (Invariantes DDD): {len(validation_errors)}")
    if validation_errors:
        print("   ⚠️  ENCONTRADOS:")
        for error_group in validation_errors:
            print(f"\n   Tipo: {error_group['tipo']}")
            for item in error_group['items'][:5]:  # Mostrar solo los primeros 5
                print(f"      - {item.item_code}: {item.item_name}")
            if len(error_group['items']) > 5:
                print(f"      ... y {len(error_group['items']) - 5} más")
    else:
        print("   ✅ No se encontraron errores de validación")
    
    print("\n" + "="*70)
    print(f"RESUMEN: {len(test_items)} items, {len(test_prescriptions)} recetas, {len(test_companies)} companies, " +
          f"{len(test_warehouses)} warehouses, {len(test_suppliers)} suppliers, {len(test_patients)} patients, " +
          f"{len(test_doctors)} doctors, {len(test_shelves)} shelves de prueba")
    print("="*70 + "\n")
    
    return {
        'test_items': len(test_items),
        'test_prescriptions': len(test_prescriptions),
        'test_companies': len(test_companies),
        'test_warehouses': len(test_warehouses),
        'test_suppliers': len(test_suppliers),
        'test_patients': len(test_patients),
        'test_doctors': len(test_doctors),
        'test_shelves': len(test_shelves),
        'incomplete_items': len(incomplete_items),
        'validation_errors': len(validation_errors)
    }


def cleanup_test_items(confirm=False):
    """
    Limpia items de prueba de la base de datos
    """
    if not confirm:
        print("⚠️  Esta función requiere confirmación explícita")
        return
    
    test_items = check_test_items()
    
    if not test_items:
        print("✅ No hay items de prueba para limpiar")
        return
    
    print(f"\n🗑️  Limpiando {len(test_items)} items de prueba...")
    
    for item in test_items:
        try:
            frappe.delete_doc("Item", item.name, force=1, ignore_permissions=True)
            print(f"   ✓ Eliminado: {item.item_code}")
        except Exception as e:
            print(f"   ✗ Error al eliminar {item.item_code}: {str(e)}")
    
    frappe.db.commit()
    print(f"\n✅ Limpieza completada. {len(test_items)} items eliminados.")


def cleanup_test_prescriptions(confirm=False):
    """
    Limpia recetas de prueba de la base de datos
    """
    if not confirm:
        print("⚠️  Esta función requiere confirmación explícita")
        return
    
    test_prescriptions = check_test_prescriptions()
    
    if not test_prescriptions:
        print("✅ No hay recetas de prueba para limpiar")
        return
    
    print(f"\n🗑️  Limpiando {len(test_prescriptions)} recetas de prueba...")
    
    for prescription in test_prescriptions:
        try:
            frappe.delete_doc("Prescription", prescription.name, force=1, ignore_permissions=True)
            print(f"   ✓ Eliminado: {prescription.name} ({prescription.patient_name})")
        except Exception as e:
            print(f"   ✗ Error al eliminar {prescription.name}: {str(e)}")
    
    frappe.db.commit()
    print(f"\n✅ Limpieza completada. {len(test_prescriptions)} recetas eliminadas.")


def cleanup_all_test_data():
    """
    Limpia todos los datos de prueba de la base de datos en orden correcto
    (dependencias primero, luego los documentos principales)
    """
    print("\n🗑️  INICIANDO LIMPIEZA DE DATOS DE PRUEBA...")
    print("="*70)
    
    # 1. Limpiar recetas (dependen de patients y doctors)
    test_prescriptions = check_test_prescriptions()
    if test_prescriptions:
        print(f"\n🗑️  Limpiando {len(test_prescriptions)} recetas de prueba...")
        for prescription in test_prescriptions:
            try:
                frappe.delete_doc("Prescription", prescription.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {prescription.name} ({prescription.patient_name})")
            except Exception as e:
                print(f"   ✗ Error al eliminar {prescription.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_prescriptions)} recetas eliminadas.")
    else:
        print("\n✅ No hay recetas de prueba para limpiar")
    
    # 2. Limpiar items
    test_items = check_test_items()
    if test_items:
        print(f"\n🗑️  Limpiando {len(test_items)} items de prueba...")
        for item in test_items:
            try:
                frappe.delete_doc("Item", item.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {item.item_code}")
            except Exception as e:
                print(f"   ✗ Error al eliminar {item.item_code}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_items)} items eliminados.")
    else:
        print("\n✅ No hay items de prueba para limpiar")
    
    # 3. Limpiar patients
    test_patients = check_test_patients()
    if test_patients:
        print(f"\n🗑️  Limpiando {len(test_patients)} patients de prueba...")
        for patient in test_patients:
            try:
                frappe.delete_doc("Patient", patient.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {patient.patient_name}")
            except Exception as e:
                print(f"   ✗ Error al eliminar {patient.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_patients)} patients eliminados.")
    else:
        print("\n✅ No hay patients de prueba para limpiar")
    
    # 4. Limpiar doctors
    test_doctors = check_test_doctors()
    if test_doctors:
        print(f"\n🗑️  Limpiando {len(test_doctors)} doctors de prueba...")
        for doctor in test_doctors:
            try:
                frappe.delete_doc("Doctor", doctor.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {doctor.doctor_name}")
            except Exception as e:
                print(f"   ✗ Error al eliminar {doctor.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_doctors)} doctors eliminados.")
    else:
        print("\n✅ No hay doctors de prueba para limpiar")
    
    # 5. Limpiar warehouses
    test_warehouses = check_test_warehouses()
    if test_warehouses:
        print(f"\n🗑️  Limpiando {len(test_warehouses)} warehouses de prueba...")
        for warehouse in test_warehouses:
            try:
                frappe.delete_doc("Warehouse", warehouse.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {warehouse.name}")
            except Exception as e:
                print(f"   ✗ Error al eliminar {warehouse.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_warehouses)} warehouses eliminados.")
    else:
        print("\n✅ No hay warehouses de prueba para limpiar")
    
    # 6. Limpiar suppliers
    test_suppliers = check_test_suppliers()
    if test_suppliers:
        print(f"\n🗑️  Limpiando {len(test_suppliers)} suppliers de prueba...")
        for supplier in test_suppliers:
            try:
                frappe.delete_doc("Supplier", supplier.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {supplier.supplier_name}")
            except Exception as e:
                print(f"   ✗ Error al eliminar {supplier.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_suppliers)} suppliers eliminados.")
    else:
        print("\n✅ No hay suppliers de prueba para limpiar")
    
    # 7. Limpiar shelves
    test_shelves = check_test_shelves()
    if test_shelves:
        print(f"\n🗑️  Limpiando {len(test_shelves)} shelves de prueba...")
        for shelf in test_shelves:
            try:
                frappe.delete_doc("Shelf", shelf.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {shelf.name} ({shelf.shelf_name})")
            except Exception as e:
                print(f"   ✗ Error al eliminar {shelf.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_shelves)} shelves eliminados.")
    else:
        print("\n✅ No hay shelves de prueba para limpiar")
    
    # 8. Limpiar Shelf Movements de prueba
    test_shelf_movements = frappe.get_all("Shelf Movement", fields=["name", "movement_type", "docstatus"])
    if test_shelf_movements:
        print(f"\n🗑️  Limpiando {len(test_shelf_movements)} Shelf Movements de prueba...")
        for sm in test_shelf_movements:
            try:
                if sm.docstatus == 1:
                    sm_doc = frappe.get_doc("Shelf Movement", sm.name)
                    sm_doc.cancel()
                frappe.delete_doc("Shelf Movement", sm.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {sm.name} ({sm.movement_type})")
            except Exception as e:
                print(f"   ✗ Error al eliminar {sm.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_shelf_movements)} Shelf Movements eliminados.")
    else:
        print("\n✅ No hay Shelf Movements de prueba para limpiar")
    
    # 9. Limpiar Stock Entries de prueba
    test_stock_entries = frappe.get_all("Stock Entry", 
        filters={"purpose": ("in", ["Material Receipt", "Material Transfer", "Material Issue"])},
        fields=["name", "purpose", "docstatus"])
    if test_stock_entries:
        print(f"\n🗑️  Limpiando {len(test_stock_entries)} Stock Entries de prueba...")
        deleted_count = 0
        for se in test_stock_entries:
            try:
                if se.docstatus == 1:
                    se_doc = frappe.get_doc("Stock Entry", se.name)
                    se_doc.cancel()
                frappe.delete_doc("Stock Entry", se.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {se.name} ({se.purpose})")
                deleted_count += 1
            except Exception as e:
                # Si falla por referencias rotas (warehouses eliminados), intentar eliminación directa
                try:
                    error_msg = str(e)
                    if "Could not find Warehouse" in error_msg or "does not exist" in error_msg:
                        # Eliminar directamente desde BD
                        frappe.db.sql("DELETE FROM `tabStock Entry` WHERE name = %s", (se.name,))
                        frappe.db.sql("DELETE FROM `tabStock Entry Detail` WHERE parent = %s", (se.name,))
                        print(f"   ✓ Eliminado (directo BD): {se.name} ({se.purpose}) - Referencias rotas")
                        deleted_count += 1
                    else:
                        print(f"   ✗ Error al eliminar {se.name}: {str(e)}")
                except Exception as e2:
                    print(f"   ✗ Error crítico al eliminar {se.name}: {str(e2)}")
        frappe.db.commit()
        print(f"✅ {deleted_count} de {len(test_stock_entries)} Stock Entries eliminados.")
    else:
        print("\n✅ No hay Stock Entries de prueba para limpiar")
    
    # 10. Limpiar Purchase Receipts de prueba
    test_purchase_receipts = frappe.get_all("Purchase Receipt", 
        filters={"supplier": ("like", "TEST-%")}, 
        fields=["name", "supplier", "docstatus", "status"])
    if test_purchase_receipts:
        print(f"\n🗑️  Limpiando {len(test_purchase_receipts)} Purchase Receipts de prueba...")
        for pr in test_purchase_receipts:
            try:
                pr_doc = frappe.get_doc("Purchase Receipt", pr.name)
                if pr_doc.docstatus == 1:
                    pr_doc.cancel()
                frappe.delete_doc("Purchase Receipt", pr.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {pr.name} ({pr.supplier})")
            except Exception as e:
                print(f"   ✗ Error al eliminar {pr.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_purchase_receipts)} Purchase Receipts eliminados.")
    else:
        print("\n✅ No hay Purchase Receipts de prueba para limpiar")
    
    # 11. Limpiar Purchase Orders de prueba
    test_purchase_orders = frappe.get_all("Purchase Order", 
        filters={"supplier": ("like", "TEST-%")}, 
        fields=["name", "supplier", "docstatus", "status"])
    if test_purchase_orders:
        print(f"\n🗑️  Limpiando {len(test_purchase_orders)} Purchase Orders de prueba...")
        for po in test_purchase_orders:
            try:
                po_doc = frappe.get_doc("Purchase Order", po.name)
                if po_doc.docstatus == 1:
                    po_doc.cancel()
                frappe.delete_doc("Purchase Order", po.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {po.name} ({po.supplier})")
            except Exception as e:
                print(f"   ✗ Error al eliminar {po.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_purchase_orders)} Purchase Orders eliminados.")
    else:
        print("\n✅ No hay Purchase Orders de prueba para limpiar")
    
    # 12. Limpiar Sales Invoices de prueba
    test_sales_invoices = frappe.get_all("Sales Invoice", 
        filters={"customer": ("like", "TEST-%")}, 
        fields=["name", "customer", "docstatus", "status"])
    if test_sales_invoices:
        print(f"\n🗑️  Limpiando {len(test_sales_invoices)} Sales Invoices de prueba...")
        for si in test_sales_invoices:
            try:
                si_doc = frappe.get_doc("Sales Invoice", si.name)
                if si_doc.docstatus == 1:
                    si_doc.cancel()
                frappe.delete_doc("Sales Invoice", si.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {si.name} ({si.customer})")
            except Exception as e:
                print(f"   ✗ Error al eliminar {si.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_sales_invoices)} Sales Invoices eliminados.")
    else:
        print("\n✅ No hay Sales Invoices de prueba para limpiar")
    
    # 13. Limpiar Purchase Invoices de prueba
    test_purchase_invoices = frappe.get_all("Purchase Invoice", 
        filters={"supplier": ("like", "TEST-%")}, 
        fields=["name", "supplier", "docstatus", "status"])
    if test_purchase_invoices:
        print(f"\n🗑️  Limpiando {len(test_purchase_invoices)} Purchase Invoices de prueba...")
        for pi in test_purchase_invoices:
            try:
                pi_doc = frappe.get_doc("Purchase Invoice", pi.name)
                if pi_doc.docstatus == 1:
                    pi_doc.cancel()
                frappe.delete_doc("Purchase Invoice", pi.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {pi.name} ({pi.supplier})")
            except Exception as e:
                print(f"   ✗ Error al eliminar {pi.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_purchase_invoices)} Purchase Invoices eliminados.")
    else:
        print("\n✅ No hay Purchase Invoices de prueba para limpiar")
    
    # 14. Limpiar companies (al final porque otros docs pueden depender)
    test_companies = check_test_companies()
    if test_companies:
        print(f"\n🗑️  Limpiando {len(test_companies)} companies de prueba...")
        for company in test_companies:
            try:
                frappe.delete_doc("Company", company.name, force=1, ignore_permissions=True)
                print(f"   ✓ Eliminado: {company.name}")
            except Exception as e:
                print(f"   ✗ Error al eliminar {company.name}: {str(e)}")
        frappe.db.commit()
        print(f"✅ {len(test_companies)} companies eliminadas.")
    else:
        print("\n✅ No hay companies de prueba para limpiar")
    
    print("\n" + "="*70)
    print("✅ Limpieza completa de datos de prueba finalizada.")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Para ejecutar desde consola de Frappe
    print_validation_report()

