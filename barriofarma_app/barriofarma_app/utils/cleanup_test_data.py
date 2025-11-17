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
    print("Limpiando Purchase Invoices...")
    pis = frappe.get_all("Purchase Invoice", filters={"name": ("like", "PI-%")}, fields=["name", "docstatus"])
    for pi in pis:
        try:
            pi_doc = frappe.get_doc("Purchase Invoice", pi.name)
            if pi_doc.docstatus == 1:
                pi_doc.cancel()
            frappe.delete_doc("Purchase Invoice", pi.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {pi.name}")
        except Exception as e:
            print(f"  ✗ Error eliminando {pi.name}: {e}")
    
    # Limpiar Purchase Receipts de prueba
    print("\nLimpiando Purchase Receipts...")
    prs = frappe.get_all("Purchase Receipt", filters={"name": ("like", "PR-%")}, fields=["name", "docstatus"])
    for pr in prs:
        try:
            pr_doc = frappe.get_doc("Purchase Receipt", pr.name)
            if pr_doc.docstatus == 1:
                pr_doc.cancel()
            frappe.delete_doc("Purchase Receipt", pr.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {pr.name}")
        except Exception as e:
            print(f"  ✗ Error eliminando {pr.name}: {e}")
    
    # Limpiar Purchase Orders de prueba
    print("\nLimpiando Purchase Orders...")
    pos = frappe.get_all("Purchase Order", filters={"name": ("like", "PO-%")}, fields=["name", "docstatus"])
    for po in pos:
        try:
            po_doc = frappe.get_doc("Purchase Order", po.name)
            if po_doc.docstatus == 1:
                po_doc.cancel()
            frappe.delete_doc("Purchase Order", po.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {po.name}")
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
    # Primero limpiar Stock Ledger Entries relacionados
    print("\nLimpiando Warehouses...")
    warehouses = frappe.get_all("Warehouse", filters={"warehouse_name": ("like", "TEST-WH-%")}, fields=["name", "warehouse_name"])
    for wh in warehouses:
        try:
            # Intentar eliminar Stock Ledger Entries relacionados primero
            sle_count = frappe.db.count("Stock Ledger Entry", {"warehouse": wh.name})
            if sle_count > 0:
                frappe.db.sql("DELETE FROM `tabStock Ledger Entry` WHERE warehouse = %s", (wh.name,))
                print(f"  ✓ Eliminados {sle_count} Stock Ledger Entries de {wh.warehouse_name}")
            
            # Intentar eliminar Bin relacionados
            bin_count = frappe.db.count("Bin", {"warehouse": wh.name})
            if bin_count > 0:
                frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse = %s", (wh.name,))
                print(f"  ✓ Eliminados {bin_count} Bins de {wh.warehouse_name}")
            
            # Ahora eliminar el warehouse
            frappe.delete_doc("Warehouse", wh.name, force=True, ignore_permissions=True)
            print(f"  ✓ Eliminado: {wh.warehouse_name}")
        except Exception as e:
            print(f"  ✗ Error eliminando {wh.warehouse_name}: {e}")
            # Si aún falla, intentar con más fuerza
            try:
                frappe.db.sql("DELETE FROM `tabWarehouse` WHERE name = %s", (wh.name,))
                print(f"  ✓ Eliminado directamente de BD: {wh.warehouse_name}")
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
    
    # Warehouses de prueba
    test_warehouses = frappe.get_all("Warehouse", filters={"warehouse_name": ("like", "TEST-WH-%")}, fields=["name", "warehouse_name", "creation"])
    print(f"\nWarehouses de prueba encontrados: {len(test_warehouses)}")
    if test_warehouses:
        for wh in test_warehouses[:10]:
            print(f"  - {wh.warehouse_name} (creado: {wh.creation})")
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
    
    # Purchase Orders de prueba
    test_pos = frappe.get_all("Purchase Order", filters={"name": ("like", "PO-%")}, fields=["name", "creation"])
    print(f"\nPurchase Orders de prueba encontrados: {len(test_pos)}")
    if test_pos:
        for po in test_pos[:10]:
            print(f"  - {po.name} (creado: {po.creation})")
        if len(test_pos) > 10:
            print(f"  ... y {len(test_pos) - 10} más")
    
    # Purchase Receipts de prueba (buscar por suppliers de prueba)
    if test_suppliers:
        supplier_names = [s.name for s in test_suppliers]
        test_prs = frappe.get_all("Purchase Receipt", filters={"supplier": ("in", supplier_names)}, fields=["name", "supplier", "creation"])
        print(f"\nPurchase Receipts de prueba encontrados: {len(test_prs)}")
        if test_prs:
            for pr in test_prs[:10]:
                print(f"  - {pr.name} (supplier: {pr.supplier}, creado: {pr.creation})")
            if len(test_prs) > 10:
                print(f"  ... y {len(test_prs) - 10} más")
    else:
        print("\nPurchase Receipts de prueba encontrados: 0")
    
    # Purchase Invoices de prueba (buscar por suppliers de prueba)
    if test_suppliers:
        supplier_names = [s.name for s in test_suppliers]
        test_pis = frappe.get_all("Purchase Invoice", filters={"supplier": ("in", supplier_names)}, fields=["name", "supplier", "creation"])
        print(f"\nPurchase Invoices de prueba encontrados: {len(test_pis)}")
        if test_pis:
            for pi in test_pis[:10]:
                print(f"  - {pi.name} (supplier: {pi.supplier}, creado: {pi.creation})")
            if len(test_pis) > 10:
                print(f"  ... y {len(test_pis) - 10} más")
    else:
        print("\nPurchase Invoices de prueba encontrados: 0")
    
    print("\n=== Resumen ===")
    print(f"Total Items: {len(test_items)}")
    print(f"Total Suppliers: {len(test_suppliers)}")
    print(f"Total Warehouses: {len(test_warehouses)}")
    print(f"Total Batches: {len(test_batches)}")
    print(f"Total Purchase Orders: {len(test_pos)}")
    print(f"Total Purchase Receipts: {len(test_prs) if test_suppliers else 0}")
    print(f"Total Purchase Invoices: {len(test_pis) if test_suppliers else 0}")


if __name__ == "__main__":
    # Ejecutar verificación primero
    check_test_data()
    
    # Preguntar si quiere limpiar
    print("\n¿Desea limpiar estos datos? (s/n): ", end="")
    # En modo interactivo, el usuario puede responder
    # Para ejecución automática, descomentar la siguiente línea:
    # cleanup_test_data()

