# -*- coding: utf-8 -*-
"""
Script para probar el reporte de trazabilidad desde consola
"""

import frappe

def test_traceability_report():
    """Probar el reporte de trazabilidad"""
    frappe.set_user("Administrator")
    
    print("\n" + "=" * 70)
    print("VALIDACIÓN DEL REPORTE DE TRAZABILIDAD")
    print("=" * 70)
    
    # Importar el módulo del reporte
    from barriofarma_app.barriofarma_app.report.traceability_report.traceability_report import execute
    
    # Ejecutar reporte con filtros
    filters = {
        "item_code": "TEST-TRACE-001",
        "from_date": "2025-01-01",
        "to_date": "2026-12-31"
    }
    
    print(f"\nEjecutando reporte con filtros:")
    print(f"  - Item: {filters['item_code']}")
    print(f"  - Desde: {filters['from_date']}")
    print(f"  - Hasta: {filters['to_date']}")
    
    columns_result, data = execute(filters)
    
    print(f"\nColumnas definidas: {len(columns_result)}")
    print("Primeras 5 columnas:")
    for i, col in enumerate(columns_result[:5], 1):
        print(f"  {i}. {col.get('label')} ({col.get('fieldname')})")
    
    print(f"\nResultados:")
    print(f"  - Columnas retornadas: {len(columns_result)}")
    print(f"  - Filas de datos: {len(data)}")
    
    if data:
        print("\nPrimeras 10 transacciones:")
        for i, row in enumerate(data[:10], 1):
            trans_type = row.get("transaction_type", "N/A")
            doc_name = row.get("document_name", "N/A")
            date = row.get("posting_date", "N/A")
            qty = row.get("quantity", "N/A")
            batch = row.get("batch_no", "N/A")
            print(f"  {i}. {trans_type:30} | Doc: {doc_name:20} | Fecha: {date} | Cantidad: {qty} | Lote: {batch}")
    else:
        print("\n⚠️  No se encontraron datos. Verificando transacciones existentes...")
        
        # Verificar si existen las transacciones
        pr_count = frappe.db.count("Purchase Receipt", filters={"supplier": "TEST-SUPPLIER-TRACE"})
        se_count = frappe.db.count("Stock Entry", filters={"stock_entry_type": "Material Transfer"})
        si_count = frappe.db.count("Sales Invoice", filters={"customer": "TEST-CUSTOMER-TRACE"})
        
        print(f"  - Purchase Receipts: {pr_count}")
        print(f"  - Stock Entries: {se_count}")
        print(f"  - Sales Invoices: {si_count}")
        
        # Verificar Purchase Receipt específico
        pr_list = frappe.get_all("Purchase Receipt", 
            filters={"supplier": "TEST-SUPPLIER-TRACE"}, 
            fields=["name", "posting_date", "docstatus"],
            limit=5
        )
        if pr_list:
            print(f"\n  Purchase Receipts encontrados:")
            for pr in pr_list:
                print(f"    - {pr.name} (Fecha: {pr.posting_date}, Estado: {pr.docstatus})")
                # Verificar items
                items = frappe.get_all("Purchase Receipt Item",
                    filters={"parent": pr.name},
                    fields=["item_code", "batch_no", "qty"]
                )
                for item in items:
                    print(f"      Item: {item.item_code}, Batch: {item.batch_no}, Qty: {item.qty}")
    
    print("\n" + "=" * 70)
    
    return columns_result, data

if __name__ == "__main__":
    test_traceability_report()

