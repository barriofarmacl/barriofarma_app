# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Validación de devoluciones de productos vendidos (Sales Return)

Story 4.5: Devoluciones de Productos Vendidos

Esta validación asegura que las devoluciones cumplan con las reglas del dominio:
- Motivo de devolución obligatorio
- Devolución dentro de plazo razonable (30 días desde venta original)
- Validación de productos vencidos (opcional, pero recomendado)
"""

import frappe
from frappe import _
from frappe.utils import getdate, today, date_diff
from datetime import timedelta


def validate_return_requirements(doc, method=None):
    """
    Validar requisitos para devoluciones de productos vendidos.
    
    Esta función se ejecuta cuando Sales Invoice tiene is_return = 1.
    
    Args:
        doc: El documento Sales Invoice con is_return = 1
        method: El método que dispara el evento (para hooks)
    
    Raises:
        frappe.ValidationError: Si la devolución no cumple con los requisitos
    """
    # Solo validar si es una devolución
    if not doc.get("is_return"):
        return
    
    # Validar motivo de devolución (obligatorio incluso si no hay items)
    return_reason = doc.get("custom_return_reason")
    if not return_reason or not return_reason.strip():
        frappe.throw(
            _("El motivo de devolución es obligatorio para procesar una devolución. Por favor, especifique el motivo."),
            title=_("Motivo de Devolución Requerido")
        )
    
    if not doc.get("items"):
        return
    
    # Validar plazo de devolución (30 días desde venta original)
    if doc.get("return_against"):
        # Obtener fecha de la venta original
        original_invoice_date = frappe.db.get_value(
            "Sales Invoice",
            doc.return_against,
            "posting_date"
        )
        
        if original_invoice_date:
            original_date = getdate(original_invoice_date)
            return_date = getdate(doc.posting_date or today())
            days_diff = date_diff(return_date, original_date)
            
            # Permitir devoluciones hasta 30 días después de la venta original
            max_return_days = 30
            if days_diff > max_return_days:
                frappe.throw(
                    _("La devolución excede el plazo permitido de {0} días desde la venta original (fecha de venta: {1}, fecha de devolución: {2}, días transcurridos: {3}). Contacte a un administrador si necesita procesar una devolución fuera de plazo.").format(
                        max_return_days,
                        original_date.strftime("%d/%m/%Y"),
                        return_date.strftime("%d/%m/%Y"),
                        days_diff
                    ),
                    title=_("Plazo de Devolución Excedido")
                )
    
    # Validar que productos devueltos no estén vencidos (advertencia, no bloquea)
    # Esto es opcional pero recomendado para mantener calidad
    current_date = getdate(today())
    expired_items = []
    
    for item in doc.items:
        batch_no = item.get("batch_no")
        if not batch_no:
            continue
        
        if not frappe.db.exists("Batch", batch_no):
            continue
        
        batch = frappe.get_doc("Batch", batch_no)
        expiry_date = batch.get("expiry_date")
        
        if expiry_date and getdate(expiry_date) < current_date:
            expired_items.append({
                "item": item.item_code,
                "batch": batch_no,
                "expiry_date": getdate(expiry_date).strftime("%d/%m/%Y")
            })
    
    if expired_items:
        expired_items_msg = ", ".join([
            f"{item['item']} (lote {item['batch']}, vencido el {item['expiry_date']})"
            for item in expired_items
        ])
        frappe.msgprint(
            _("Advertencia: Los siguientes productos devueltos están vencidos: {0}. Se recomienda verificar el estado de estos productos antes de aceptarlos en inventario.").format(
                expired_items_msg
            ),
            indicator="orange",
            title=_("Productos Vencidos en Devolución")
        )


def validate_return_permissions(doc, method=None):
    """
    Validar permisos para realizar devoluciones.
    
    Solo usuarios con roles específicos pueden realizar devoluciones.
    
    Args:
        doc: El documento Sales Invoice con is_return = 1
        method: El método que dispara el evento (para hooks)
    
    Raises:
        frappe.ValidationError: Si el usuario no tiene permisos para devoluciones
    """
    if not doc.get("is_return"):
        return
    
    user_roles = frappe.get_roles(frappe.session.user)
    
    # Roles permitidos para realizar devoluciones
    allowed_roles = [
        "System Manager",
        "Farmacéutico",
        "Sales Manager",
        "Accounts Manager"
    ]
    
    has_permission = any(role in user_roles for role in allowed_roles)
    
    if not has_permission:
        frappe.throw(
            _("No tiene permisos para realizar devoluciones. Solo usuarios con roles de Farmacéutico, Sales Manager, Accounts Manager o System Manager pueden procesar devoluciones. Contacte a un administrador si necesita realizar una devolución."),
            title=_("Permisos Insuficientes para Devolución")
        )

