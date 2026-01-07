# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Validación de productos vencidos para ventas (Sales Invoice y POS Invoice)

FR12: Prevenir venta de productos vencidos

Esta validación asegura que no se vendan productos cuya fecha de caducidad
ya ha pasado, protegiendo la salud de los pacientes.
"""

import frappe
from frappe import _
from frappe.utils import getdate, today


def validate_expired_products_in_invoice(doc, method=None):
    """
    Validar que no se vendan productos vencidos.
    
    Esta función puede ser llamada:
    - Desde el método validate() de Sales Invoice (override)
    - Desde un doc_events hook para POS Invoice
    
    Args:
        doc: El documento (Sales Invoice o POS Invoice)
        method: El método que dispara el evento (para hooks)
    
    Raises:
        frappe.ValidationError: Si se intenta vender un producto vencido
    """
    if not doc.get("items"):
        return
    
    current_date = getdate(today())
    
    for item in doc.items:
        # Solo validar items con lote asignado
        batch_no = item.get("batch_no")
        if not batch_no:
            continue
        
        # Obtener información del batch
        if not frappe.db.exists("Batch", batch_no):
            continue
        
        batch = frappe.get_doc("Batch", batch_no)
        expiry_date = batch.get("expiry_date")
        
        # Si el batch tiene fecha de caducidad y está vencido
        if expiry_date and getdate(expiry_date) < current_date:
            # Formatear fecha para el mensaje
            expiry_date_formatted = getdate(expiry_date).strftime("%d/%m/%Y")
            
            frappe.throw(
                _("El producto {0} del lote {1} está vencido (caducó el {2}). No se permite la venta de productos vencidos.").format(
                    frappe.bold(item.item_code),
                    frappe.bold(batch_no),
                    frappe.bold(expiry_date_formatted)
                ),
                title=_("Producto Vencido - Venta No Permitida")
            )


def validate_pos_invoice_expired_products(doc, method):
    """
    Hook para validar productos vencidos en POS Invoice.
    
    Se ejecuta durante el evento 'validate' de POS Invoice.
    
    Args:
        doc: El documento POS Invoice
        method: El método que dispara el evento ('validate')
    """
    validate_expired_products_in_invoice(doc, method)

