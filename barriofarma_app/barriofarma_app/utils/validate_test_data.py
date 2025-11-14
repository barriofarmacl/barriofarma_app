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
    
    # 2. Items incompletos
    incomplete_items = check_incomplete_items()
    print(f"\n2. Items con Campos Custom Incompletos: {len(incomplete_items)}")
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
    
    # 3. Errores de validación
    validation_errors = check_validation_errors()
    print(f"\n3. Errores de Validación (Invariantes DDD): {len(validation_errors)}")
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
    print(f"RESUMEN: {len(test_items)} items de prueba, {len(incomplete_items)} incompletos, {len(validation_errors)} tipos de errores")
    print("="*70 + "\n")
    
    return {
        'test_items': len(test_items),
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


if __name__ == "__main__":
    # Para ejecutar desde consola de Frappe
    print_validation_report()

