# -*- coding: utf-8 -*-
"""Obtener nombres reales de shelves de prueba"""
import frappe

def get_test_shelves():
    """Obtiene los nombres reales de los shelves de prueba."""
    shelves = frappe.get_all(
        'Shelf',
        filters={
            'warehouse': 'Stores - BF',
            'location_code': ['in', ['A1', 'B2']]
        },
        fields=['name', 'location_code'],
        order_by='location_code'
    )
    
    print("\n" + "=" * 70)
    print("SHELVES DE PRUEBA ENCONTRADOS")
    print("=" * 70)
    
    for shelf in shelves:
        print(f"  {shelf.name} - location_code: {shelf.location_code}")
    
    print("=" * 70)
    
    return {s.location_code: s.name for s in shelves}

