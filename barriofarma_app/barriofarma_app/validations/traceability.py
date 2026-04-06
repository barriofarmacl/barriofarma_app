# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Validaciones de Trazabilidad

Story 2.1: Validación de Trazabilidad Completa en Ventas

Este módulo proporciona funciones para validar que los productos vendidos
tengan trazabilidad completa (lote y fecha de caducidad) según normativa
farmacéutica chilena.

FR37: Registrar lote y fecha de caducidad de cada producto vendido
FR38: Rastrear medicamento desde recepción hasta venta
"""

import frappe
from frappe import _


def validate_batch_required_for_sale(doc, items_field="items"):
    """
    Validar que items con has_batch_no=1 tengan batch_no y expiry_date
    
    Story 2.1: Validación de Trazabilidad Completa en Ventas
    
    FR37: Registrar lote y fecha de caducidad de cada producto vendido
    
    Esta función valida que:
    1. Items con has_batch_no=1 requieren batch_no obligatorio
    2. El Batch debe tener expiry_date registrado
    
    Args:
        doc: El documento (Sales Invoice, POS Invoice, etc.)
        items_field: Nombre del campo que contiene los items (default: "items")
    
    Raises:
        frappe.ValidationError: Si un item con has_batch_no=1 no tiene batch_no
        frappe.ValidationError: Si el Batch no tiene expiry_date
    """
    if not hasattr(doc, items_field):
        return
    
    # Obtener items usando get() para asegurar que obtenemos la lista, no el método
    items = doc.get(items_field, [])
    if not items:
        return
    
    # Si items es un método (callable), llamarlo
    if callable(items):
        items = items()
    
    for item in items:
        item_code = item.get("item_code")
        if not item_code:
            continue
        
        # Obtener información del Item
        if not frappe.db.exists("Item", item_code):
            continue
        
        item_doc = frappe.get_doc("Item", item_code)
        
        # Si el item requiere lote (has_batch_no=1), validar que tenga batch_no
        if item_doc.get("has_batch_no") == 1:
            batch_no = item.get("batch_no")
            
            if not batch_no:
                frappe.throw(
                    _("El producto '{0}' requiere lote (batch_no) para la venta según normativa de trazabilidad. "
                      "Debe seleccionar un lote antes de guardar el documento.").format(
                        frappe.bold(item_code)
                    ),
                    title=_("Lote Requerido para Trazabilidad")
                )
            
            # Validar que el Batch existe y tiene expiry_date
            if not frappe.db.exists("Batch", batch_no):
                frappe.throw(
                    _("El lote '{0}' especificado para el producto '{1}' no existe en el sistema.").format(
                        frappe.bold(batch_no),
                        frappe.bold(item_code)
                    ),
                    title=_("Lote Inválido")
                )
            
            batch_doc = frappe.get_doc("Batch", batch_no)
            
            if not batch_doc.get("expiry_date"):
                frappe.throw(
                    _("El lote '{0}' del producto '{1}' debe tener fecha de caducidad (expiry_date) registrada "
                      "para cumplir con normativa de trazabilidad. Contacte al administrador para registrar "
                      "la fecha de caducidad del lote.").format(
                        frappe.bold(batch_no),
                        frappe.bold(item_code)
                    ),
                    title=_("Fecha de Caducidad Requerida")
                )

