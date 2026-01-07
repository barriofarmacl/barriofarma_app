# -*- coding: utf-8 -*-
"""
Setup de datos de prueba para reporte de trazabilidad

Story 2.2: Reporte de Trazabilidad de Medicamento

Este script crea datos de prueba completos para probar el reporte de trazabilidad:
- Item con has_batch_no=1
- Batch con expiry_date
- Purchase Receipt (recepción inicial)
- Stock Entry (movimiento de stock)
- Sales Invoice (venta)

Uso:
    bench --site barriofarma.localhost execute \
        barriofarma_app.barriofarma_app.utils.setup_traceability_test_data.create_traceability_test_data
"""

import frappe
from frappe.utils import today, add_days, getdate
from datetime import datetime

# Constantes para datos de prueba
TEST_ITEM_CODE = "TEST-TRACE-001"
TEST_BATCH_NO = "BATCH-TRACE-001"
TEST_SUPPLIER_NAME = "TEST-SUPPLIER-TRACE"
TEST_CUSTOMER_NAME = "TEST-CUSTOMER-TRACE"
TEST_WAREHOUSE = "Stores - BF"
TEST_WAREHOUSE_TO = "Finished Goods - BF"


def create_traceability_test_data():
    """
    Crear datos de prueba completos para reporte de trazabilidad
    """
    print("\n" + "=" * 70)
    print("CREACION DE DATOS DE PRUEBA PARA REPORTE DE TRAZABILIDAD")
    print("=" * 70)
    
    frappe.set_user("Administrator")
    
    created = {}
    errors = []
    
    try:
        # 1. Crear Item con has_batch_no=1
        print("\n1. Creando Item con lote...")
        if not frappe.db.exists("Item", TEST_ITEM_CODE):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": TEST_ITEM_CODE,
                "item_name": "Medicamento de Prueba Trazabilidad",
                "item_group": "Products",
                "stock_uom": "Nos",
                "is_stock_item": 1,
                "has_batch_no": 1,
                "has_expiry_date": 1,
                "create_new_batch": 1,
                "custom_dispensing_type": "Venta Libre",
                "custom_control_level": "None"
            })
            item.insert()
            frappe.db.commit()
            created["item"] = item.name
            print(f"   ✅ Item creado: {item.name}")
        else:
            created["item"] = TEST_ITEM_CODE
            # Asegurar que el item tiene has_batch_no=1 (actualizar directamente en DB)
            frappe.db.set_value("Item", TEST_ITEM_CODE, "has_batch_no", 1)
            frappe.db.set_value("Item", TEST_ITEM_CODE, "has_expiry_date", 1)
            frappe.db.commit()
            print(f"   ✅ Item actualizado: {TEST_ITEM_CODE} (has_batch_no=1)")
        
        # Verificar que el Item tiene has_batch_no=1 antes de crear Batch
        item_has_batch = frappe.db.get_value("Item", TEST_ITEM_CODE, "has_batch_no")
        if item_has_batch != 1:
            raise Exception(f"Item {TEST_ITEM_CODE} no tiene has_batch_no=1. Valor actual: {item_has_batch}")
        
        # 2. Crear Batch (después de que el Item esté guardado y verificado)
        print("\n2. Creando Batch...")
        if not frappe.db.exists("Batch", TEST_BATCH_NO):
            batch = frappe.get_doc({
                "doctype": "Batch",
                "batch_id": TEST_BATCH_NO,
                "item": TEST_ITEM_CODE,
                "expiry_date": add_days(today(), 365)  # Caduca en 1 año
            })
            batch.insert()
            frappe.db.commit()
            created["batch"] = batch.name
            print(f"   ✅ Batch creado: {batch.name} (expiry_date: {batch.expiry_date})")
        else:
            created["batch"] = TEST_BATCH_NO
            print(f"   ℹ️  Batch ya existe: {TEST_BATCH_NO}")
        
        # 3. Crear Supplier
        print("\n3. Creando Supplier...")
        if not frappe.db.exists("Supplier", TEST_SUPPLIER_NAME):
            # Obtener el primer Supplier Group disponible
            supplier_group = frappe.get_all("Supplier Group", limit=1)
            supplier_group_name = supplier_group[0].name if supplier_group else "All Supplier Groups"
            
            supplier = frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": TEST_SUPPLIER_NAME,
                "supplier_group": supplier_group_name
            })
            supplier.insert()
            frappe.db.commit()
            created["supplier"] = supplier.name
            print(f"   ✅ Supplier creado: {supplier.name}")
        else:
            created["supplier"] = TEST_SUPPLIER_NAME
            print(f"   ℹ️  Supplier ya existe: {TEST_SUPPLIER_NAME}")
        
        # 4. Crear Customer
        print("\n4. Creando Customer...")
        if not frappe.db.exists("Customer", TEST_CUSTOMER_NAME):
            # Obtener el primer Customer Group y Territory disponibles
            customer_group = frappe.get_all("Customer Group", limit=1)
            customer_group_name = customer_group[0].name if customer_group else "All Customer Groups"
            
            territory = frappe.get_all("Territory", limit=1)
            territory_name = territory[0].name if territory else "All Territories"
            
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": TEST_CUSTOMER_NAME,
                "customer_group": customer_group_name,
                "territory": territory_name
            })
            customer.insert()
            frappe.db.commit()
            created["customer"] = customer.name
            print(f"   ✅ Customer creado: {customer.name}")
        else:
            created["customer"] = TEST_CUSTOMER_NAME
            print(f"   ℹ️  Customer ya existe: {TEST_CUSTOMER_NAME}")
        
        # 5. Crear Purchase Receipt (Recepción inicial)
        print("\n5. Creando Purchase Receipt...")
        pr_name = f"PR-TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        if not frappe.db.exists("Purchase Receipt", pr_name):
            pr = frappe.get_doc({
                "doctype": "Purchase Receipt",
                "supplier": TEST_SUPPLIER_NAME,
                "posting_date": add_days(today(), -30),  # Hace 30 días
                "company": frappe.defaults.get_defaults().get("company") or "Barrio Farma",
                "items": [{
                    "item_code": TEST_ITEM_CODE,
                    "qty": 100,
                    "rate": 1000,
                    "warehouse": TEST_WAREHOUSE,
                    "batch_no": TEST_BATCH_NO,
                    "custom_qc_status": "Aceptado"
                }]
            })
            pr.insert()
            pr.submit()
            frappe.db.commit()
            created["purchase_receipt"] = pr.name
            print(f"   ✅ Purchase Receipt creado y enviado: {pr.name}")
        else:
            created["purchase_receipt"] = pr_name
            print(f"   ℹ️  Purchase Receipt ya existe: {pr_name}")
        
        # 6. Crear Stock Entry (Movimiento de stock)
        print("\n6. Creando Stock Entry (movimiento)...")
        se_name = f"SE-TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        if not frappe.db.exists("Stock Entry", se_name):
            se = frappe.get_doc({
                "doctype": "Stock Entry",
                "stock_entry_type": "Material Transfer",
                "posting_date": add_days(today(), -20),  # Hace 20 días
                "company": frappe.defaults.get_defaults().get("company") or "Barrio Farma",
                "items": [{
                    "item_code": TEST_ITEM_CODE,
                    "qty": 50,
                    "s_warehouse": TEST_WAREHOUSE,
                    "t_warehouse": TEST_WAREHOUSE_TO if frappe.db.exists("Warehouse", TEST_WAREHOUSE_TO) else TEST_WAREHOUSE,
                    "batch_no": TEST_BATCH_NO
                }]
            })
            se.insert()
            se.submit()
            frappe.db.commit()
            created["stock_entry"] = se.name
            print(f"   ✅ Stock Entry creado y enviado: {se.name}")
        else:
            created["stock_entry"] = se_name
            print(f"   ℹ️  Stock Entry ya existe: {se_name}")
        
        # 7. Crear Sales Invoice (Venta)
        print("\n7. Creando Sales Invoice (venta)...")
        si_name = f"SI-TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        if not frappe.db.exists("Sales Invoice", si_name):
            si = frappe.get_doc({
                "doctype": "Sales Invoice",
                "customer": TEST_CUSTOMER_NAME,
                "posting_date": add_days(today(), -10),  # Hace 10 días
                "company": frappe.defaults.get_defaults().get("company") or "Barrio Farma",
                "items": [{
                    "item_code": TEST_ITEM_CODE,
                    "qty": 25,
                    "rate": 1500,
                    "warehouse": TEST_WAREHOUSE,
                    "batch_no": TEST_BATCH_NO
                }]
            })
            si.insert()
            si.submit()
            frappe.db.commit()
            created["sales_invoice"] = si.name
            print(f"   ✅ Sales Invoice creado y enviado: {si.name}")
        else:
            created["sales_invoice"] = si_name
            print(f"   ℹ️  Sales Invoice ya existe: {si_name}")
        
        # Resumen
        print("\n" + "=" * 70)
        print("RESUMEN DE DATOS CREADOS")
        print("=" * 70)
        print(f"Item: {created.get('item')}")
        print(f"Batch: {created.get('batch')}")
        print(f"Supplier: {created.get('supplier')}")
        print(f"Customer: {created.get('customer')}")
        print(f"Purchase Receipt: {created.get('purchase_receipt')}")
        print(f"Stock Entry: {created.get('stock_entry')}")
        print(f"Sales Invoice: {created.get('sales_invoice')}")
        print("\n" + "=" * 70)
        print("PARA PROBAR EL REPORTE:")
        print("=" * 70)
        print(f"1. Ir a Reportes → Traceability Report")
        print(f"2. Filtrar por Producto: {TEST_ITEM_CODE}")
        print(f"   O filtrar por Lote: {TEST_BATCH_NO}")
        print(f"3. Ejecutar el reporte")
        print("=" * 70)
        
        return created
        
    except Exception as e:
        errors.append(str(e))
        frappe.log_error(
            message=f"Error creando datos de prueba de trazabilidad: {str(e)}",
            title="Error en setup_traceability_test_data"
        )
        print(f"\n❌ ERROR: {str(e)}")
        raise


def cleanup_traceability_test_data():
    """
    Limpiar datos de prueba de trazabilidad
    """
    print("\n" + "=" * 70)
    print("LIMPIEZA DE DATOS DE PRUEBA DE TRAZABILIDAD")
    print("=" * 70)
    
    frappe.set_user("Administrator")
    
    deleted = []
    errors = []
    
    # Eliminar en orden inverso (dependencias primero)
    try:
        # Sales Invoice
        si_list = frappe.get_all("Sales Invoice", filters={"customer": TEST_CUSTOMER_NAME}, pluck="name")
        for si_name in si_list:
            try:
                si = frappe.get_doc("Sales Invoice", si_name)
                if si.docstatus == 1:
                    si.cancel()
                si.delete()
                deleted.append(f"Sales Invoice: {si_name}")
            except Exception as e:
                errors.append(f"Sales Invoice {si_name}: {str(e)}")
        
        # Stock Entry
        se_list = frappe.get_all("Stock Entry", filters={"stock_entry_type": "Material Transfer"}, pluck="name")
        for se_name in se_list[:5]:  # Limitar a 5 para no eliminar todos
            try:
                se = frappe.get_doc("Stock Entry", se_name)
                if se.docstatus == 1:
                    se.cancel()
                se.delete()
                deleted.append(f"Stock Entry: {se_name}")
            except Exception as e:
                errors.append(f"Stock Entry {se_name}: {str(e)}")
        
        # Purchase Receipt
        pr_list = frappe.get_all("Purchase Receipt", filters={"supplier": TEST_SUPPLIER_NAME}, pluck="name")
        for pr_name in pr_list:
            try:
                pr = frappe.get_doc("Purchase Receipt", pr_name)
                if pr.docstatus == 1:
                    pr.cancel()
                pr.delete()
                deleted.append(f"Purchase Receipt: {pr_name}")
            except Exception as e:
                errors.append(f"Purchase Receipt {pr_name}: {str(e)}")
        
        # Batch
        if frappe.db.exists("Batch", TEST_BATCH_NO):
            try:
                frappe.delete_doc("Batch", TEST_BATCH_NO, force=1)
                deleted.append(f"Batch: {TEST_BATCH_NO}")
            except Exception as e:
                errors.append(f"Batch {TEST_BATCH_NO}: {str(e)}")
        
        # Item
        if frappe.db.exists("Item", TEST_ITEM_CODE):
            try:
                frappe.delete_doc("Item", TEST_ITEM_CODE, force=1)
                deleted.append(f"Item: {TEST_ITEM_CODE}")
            except Exception as e:
                errors.append(f"Item {TEST_ITEM_CODE}: {str(e)}")
        
        # Customer
        if frappe.db.exists("Customer", TEST_CUSTOMER_NAME):
            try:
                frappe.delete_doc("Customer", TEST_CUSTOMER_NAME, force=1)
                deleted.append(f"Customer: {TEST_CUSTOMER_NAME}")
            except Exception as e:
                errors.append(f"Customer {TEST_CUSTOMER_NAME}: {str(e)}")
        
        # Supplier
        if frappe.db.exists("Supplier", TEST_SUPPLIER_NAME):
            try:
                frappe.delete_doc("Supplier", TEST_SUPPLIER_NAME, force=1)
                deleted.append(f"Supplier: {TEST_SUPPLIER_NAME}")
            except Exception as e:
                errors.append(f"Supplier {TEST_SUPPLIER_NAME}: {str(e)}")
        
        frappe.db.commit()
        
        print(f"\n✅ Eliminados {len(deleted)} documentos")
        if errors:
            print(f"\n⚠️  Errores ({len(errors)}):")
            for e in errors:
                print(f"   - {e}")
        
    except Exception as e:
        frappe.log_error(
            message=f"Error limpiando datos de prueba de trazabilidad: {str(e)}",
            title="Error en cleanup_traceability_test_data"
        )
        print(f"\n❌ ERROR: {str(e)}")
        raise

