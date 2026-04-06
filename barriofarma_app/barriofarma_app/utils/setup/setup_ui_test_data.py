# -*- coding: utf-8 -*-
"""
Setup de datos de prueba para tests UI / UAT manual (consumido desde repo E2E barriofarma-e2e o bench execute)

Uso:
    bench --site barriofarma.localhost execute \
        barriofarma_app.barriofarma_app.utils.setup.setup_ui_test_data.create_ui_test_data

Para limpiar:
    bench --site barriofarma.localhost execute \
        barriofarma_app.barriofarma_app.utils.setup.setup_ui_test_data.cleanup_ui_test_data
"""
import frappe
from barriofarma_app.barriofarma_app.test_setup import (
    create_test_item,
    create_test_supplier,
    create_test_customer,
    create_test_shelf,
    create_test_warehouse,
    get_test_company,
    ensure_minimum_masters
)

# Constantes para datos de prueba UI
TEST_ITEM_CODE = "TEST-ITEM-001"
TEST_SUPPLIER_NAME = "TEST-SUPPLIER"
TEST_CUSTOMER_NAME = "TEST-CUSTOMER"
TEST_SHELF_A1 = "TEST-SHELF-A1"
TEST_SHELF_B2 = "TEST-SHELF-B2"
TEST_WAREHOUSE_NAME = "Stores - BF"


def create_ui_test_data():
    """
    Crea todos los datos de prueba necesarios para tests UI.
    """
    print("\n" + "=" * 70)
    print("CREACION DE DATOS DE PRUEBA PARA TESTS UI")
    print("=" * 70)
    
    ensure_minimum_masters()
    
    created = {}
    errors = []
    
    # 1. Crear Item de prueba
    try:
        if not frappe.db.exists("Item", TEST_ITEM_CODE):
            item = create_test_item(
                item_code=TEST_ITEM_CODE,
                item_name="Producto de Prueba UI",
                is_stock_item=1,
                has_batch_no=0,
                has_expiry_date=0,
                custom_dispensing_type="Venta Libre"
            )
            created["item"] = item.name
            print(f"Item creado: {item.name}")
        else:
            created["item"] = TEST_ITEM_CODE
            print(f"Item ya existe: {TEST_ITEM_CODE}")
    except Exception as e:
        errors.append(f"Item: {str(e)}")
        print(f"Error creando Item: {str(e)}")
    
    # 2. Crear Supplier de prueba
    try:
        if not frappe.db.exists("Supplier", TEST_SUPPLIER_NAME):
            supplier = create_test_supplier(TEST_SUPPLIER_NAME)
            created["supplier"] = supplier.name
            print(f"Supplier creado: {supplier.name}")
        else:
            created["supplier"] = TEST_SUPPLIER_NAME
            print(f"Supplier ya existe: {TEST_SUPPLIER_NAME}")
    except Exception as e:
        errors.append(f"Supplier: {str(e)}")
        print(f"Error creando Supplier: {str(e)}")
    
    # 3. Crear Customer de prueba
    try:
        if not frappe.db.exists("Customer", TEST_CUSTOMER_NAME):
            customer = create_test_customer(TEST_CUSTOMER_NAME)
            created["customer"] = customer.name
            print(f"Customer creado: {customer.name}")
        else:
            created["customer"] = TEST_CUSTOMER_NAME
            print(f"Customer ya existe: {TEST_CUSTOMER_NAME}")
    except Exception as e:
        errors.append(f"Customer: {str(e)}")
        print(f"Error creando Customer: {str(e)}")
    
    # 4. Verificar/Crear Warehouse
    try:
        if not frappe.db.exists("Warehouse", TEST_WAREHOUSE_NAME):
            warehouse = create_test_warehouse(TEST_WAREHOUSE_NAME)
            created["warehouse"] = warehouse.name
            print(f"Warehouse creado: {warehouse.name}")
        else:
            created["warehouse"] = TEST_WAREHOUSE_NAME
            print(f"Warehouse ya existe: {TEST_WAREHOUSE_NAME}")
    except Exception as e:
        errors.append(f"Warehouse: {str(e)}")
        print(f"Error creando Warehouse: {str(e)}")
    
    # 5. Crear Shelves de prueba
    warehouse = created.get("warehouse", TEST_WAREHOUSE_NAME)
    
    try:
        if not frappe.db.exists("Shelf", TEST_SHELF_A1):
            shelf_a1 = create_test_shelf(
                shelf_name="Estante A1 Prueba",
                warehouse=warehouse,
                location_code="A1",
                shelf_type="Normal",
                capacity_mode="Dinámica"
            )
            created["shelf_a1"] = shelf_a1.name
            print(f"Shelf creado: {shelf_a1.name} (A1)")
        else:
            created["shelf_a1"] = TEST_SHELF_A1
            print(f"Shelf ya existe: {TEST_SHELF_A1}")
    except Exception as e:
        errors.append(f"Shelf A1: {str(e)}")
        print(f"Error creando Shelf A1: {str(e)}")
    
    try:
        if not frappe.db.exists("Shelf", TEST_SHELF_B2):
            shelf_b2 = create_test_shelf(
                shelf_name="Estante B2 Prueba",
                warehouse=warehouse,
                location_code="B2",
                shelf_type="Normal",
                capacity_mode="Dinámica"
            )
            created["shelf_b2"] = shelf_b2.name
            print(f"Shelf creado: {shelf_b2.name} (B2)")
        else:
            created["shelf_b2"] = TEST_SHELF_B2
            print(f"Shelf ya existe: {TEST_SHELF_B2}")
    except Exception as e:
        errors.append(f"Shelf B2: {str(e)}")
        print(f"Error creando Shelf B2: {str(e)}")
    
    frappe.db.commit()
    
    # Resumen
    print("\n" + "-" * 70)
    print("RESUMEN")
    print("-" * 70)
    print(f"Datos creados/verificados: {len(created)}")
    for key, value in created.items():
        print(f"  - {key}: {value}")
    
    if errors:
        print(f"\nErrores ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    
    print("=" * 70)
    
    return {"created": created, "errors": errors}


def cleanup_ui_test_data():
    """
    Limpia los datos de prueba creados para tests UI.
    """
    print("\n" + "=" * 70)
    print("LIMPIEZA DE DATOS DE PRUEBA PARA TESTS UI")
    print("=" * 70)
    
    deleted = []
    errors = []
    
    # Orden de eliminación (respetar dependencias)
    cleanup_order = [
        ("Shelf", TEST_SHELF_A1),
        ("Shelf", TEST_SHELF_B2),
        ("Customer", TEST_CUSTOMER_NAME),
        ("Supplier", TEST_SUPPLIER_NAME),
        ("Item", TEST_ITEM_CODE),
        # Warehouse se limpia con cleanup_test_data general
    ]
    
    for doctype, name in cleanup_order:
        try:
            if frappe.db.exists(doctype, name):
                frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
                deleted.append(f"{doctype}: {name}")
                print(f"Eliminado: {doctype} - {name}")
        except Exception as e:
            errors.append(f"{doctype} {name}: {str(e)}")
            print(f"Error eliminando {doctype} {name}: {str(e)}")
    
    frappe.db.commit()
    
    print("\n" + "-" * 70)
    print("RESUMEN")
    print("-" * 70)
    print(f"Eliminados: {len(deleted)}")
    for d in deleted:
        print(f"  - {d}")
    
    if errors:
        print(f"\nErrores ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    
    print("=" * 70)
    
    return {"deleted": deleted, "errors": errors}


def get_ui_test_data_status():
    """
    Muestra el estado de los datos de prueba para tests UI.
    """
    print("\n" + "=" * 70)
    print("ESTADO DE DATOS DE PRUEBA PARA TESTS UI")
    print("=" * 70)
    
    test_data = {
        "Item": TEST_ITEM_CODE,
        "Supplier": TEST_SUPPLIER_NAME,
        "Customer": TEST_CUSTOMER_NAME,
        "Warehouse": TEST_WAREHOUSE_NAME,
        "Shelf A1": TEST_SHELF_A1,
        "Shelf B2": TEST_SHELF_B2,
    }
    
    for label, name in test_data.items():
        exists = frappe.db.exists(label.split()[0], name)
        status = "EXISTE" if exists else "NO EXISTE"
        print(f"{label:20} {name:30} [{status}]")
    
    print("=" * 70)

