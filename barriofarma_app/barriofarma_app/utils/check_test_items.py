# -*- coding: utf-8 -*-
"""Verificar items de prueba"""
import frappe

def check_test_items():
    """Verifica items de prueba."""
    items = frappe.get_all('Item', 
        filters={'item_code': ['like', 'TEST-%']}, 
        fields=['item_code', 'item_name', 'disabled']
    )
    
    print("\n" + "=" * 70)
    print("ITEMS DE PRUEBA ENCONTRADOS")
    print("=" * 70)
    
    for item in items:
        status = "DESHABILITADO" if item.disabled else "ACTIVO"
        print(f"  {item.item_code:20} - {item.item_name:30} [{status}]")
    
    print(f"\nTotal: {len(items)} items")
    print("=" * 70)
    
    return items

