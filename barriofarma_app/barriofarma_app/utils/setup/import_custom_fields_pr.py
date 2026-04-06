# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Script para importar campos custom de Purchase Receipt Item
Ejecutar con: bench --site [sitename] execute barriofarma_app.barriofarma_app.utils.setup.import_custom_fields_pr.import_custom_fields
"""

import json
import frappe
from pathlib import Path


def import_custom_fields():
    """Importar campos custom desde JSON"""
    # Ruta al archivo JSON
    json_path = Path(__file__).parent.parent.parent / "custom" / "custom_fields_purchase_receipt_item.json"
    
    if not json_path.exists():
        frappe.throw(f"Archivo no encontrado: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        fields = json.load(f)
    
    created = []
    existing = []
    
    for field_data in fields:
        field_name = field_data.get("name")
        
        if not frappe.db.exists("Custom Field", field_name):
            field = frappe.get_doc(field_data)
            field.insert(ignore_permissions=True)
            created.append(field_name)
            print(f"✅ Creado campo: {field_name}")
        else:
            existing.append(field_name)
            print(f"⏭️  Campo ya existe: {field_name}")
    
    frappe.db.commit()
    
    print(f"\n📊 Resumen:")
    print(f"   - Creados: {len(created)}")
    print(f"   - Existentes: {len(existing)}")
    print(f"\n✅ Campos custom importados exitosamente")

