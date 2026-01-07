# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Utilidades para agregar items de receta a ventas

Story 5.3: Asociación de Receta a Múltiples Medicamentos

Funcionalidad para agregar todos los medicamentos de una receta automáticamente
a una venta (Sales Invoice o POS Invoice).
"""

import frappe
from frappe import _
from frappe.utils import flt


def get_prescription_items(prescription_name):
    """
    Obtener todos los items de una receta.
    
    Args:
        prescription_name: Nombre de la receta (Prescription)
    
    Returns:
        Lista de diccionarios con información de los items de la receta
    """
    if not frappe.db.exists("Prescription", prescription_name):
        frappe.throw(
            _("La receta '{0}' no existe.").format(prescription_name),
            title=_("Receta No Encontrada")
        )
    
    try:
        prescription = frappe.get_doc("Prescription", prescription_name)
    except frappe.DoesNotExistError:
        frappe.throw(
            _("La receta '{0}' no existe.").format(prescription_name),
            title=_("Receta No Encontrada")
        )
    
    items = []
    for prescription_item in prescription.get("items", []):
        item_code = prescription_item.get("item")
        quantity = flt(prescription_item.get("quantity", 0))
        
        if not item_code or quantity <= 0:
            continue
        
        # Obtener información del item
        try:
            item_doc = frappe.get_doc("Item", item_code)
        except frappe.DoesNotExistError:
            frappe.log_error(
                message=f"Item {item_code} de receta {prescription_name} no existe",
                title="Error al Obtener Items de Receta"
            )
            continue
        
        items.append({
            "item_code": item_code,
            "item_name": item_doc.item_name,
            "quantity": quantity,
            "uom": item_doc.stock_uom or "Unit",
            "rate": item_doc.standard_rate or 0,
            "prescription_item_name": prescription_item.name
        })
    
    return items


def add_prescription_items_to_invoice(invoice_name, prescription_name, warehouse=None):
    """
    Agregar todos los items de una receta a una venta (Sales Invoice o POS Invoice).
    
    Esta función puede ser llamada desde el cliente (JavaScript) o desde el servidor.
    
    Args:
        invoice_name: Nombre de la venta (Sales Invoice o POS Invoice)
        prescription_name: Nombre de la receta (Prescription)
        warehouse: Warehouse opcional para los items
    
    Returns:
        Diccionario con información sobre los items agregados
    """
    # Validar que la venta existe
    invoice_doctype = None
    if frappe.db.exists("Sales Invoice", invoice_name):
        invoice_doctype = "Sales Invoice"
    elif frappe.db.exists("POS Invoice", invoice_name):
        invoice_doctype = "POS Invoice"
    else:
        frappe.throw(
            _("La venta '{0}' no existe.").format(invoice_name),
            title=_("Venta No Encontrada")
        )
    
    # Obtener items de la receta
    prescription_items = get_prescription_items(prescription_name)
    
    if not prescription_items:
        frappe.throw(
            _("La receta '{0}' no tiene medicamentos prescritos.").format(prescription_name),
            title=_("Receta Sin Items")
        )
    
    # Obtener documento de venta
    invoice = frappe.get_doc(invoice_doctype, invoice_name)
    
    # Validar que la receta no está ya asociada a otra venta (opcional, puede permitirse)
    # Por ahora, solo verificamos que la receta esté vigente
    
    # Agregar items de la receta a la venta
    items_added = []
    items_skipped = []
    
    for prescription_item in prescription_items:
        item_code = prescription_item["item_code"]
        quantity = prescription_item["quantity"]
        
        # Verificar si el item ya está en la venta
        item_exists = False
        for existing_item in invoice.get("items", []):
            if existing_item.item_code == item_code:
                item_exists = True
                # Actualizar cantidad si es necesario (sumar o usar la mayor)
                # Por ahora, no actualizamos si ya existe
                items_skipped.append({
                    "item_code": item_code,
                    "reason": "Item ya existe en la venta"
                })
                break
        
        if not item_exists:
            # Crear nuevo item para la venta
            item_dict = {
                "item_code": item_code,
                "item_name": prescription_item["item_name"],
                "qty": quantity,
                "uom": prescription_item["uom"],
                "rate": prescription_item["rate"],
                "warehouse": warehouse or invoice.get("set_warehouse")
            }
            
            invoice.append("items", item_dict)
            items_added.append({
                "item_code": item_code,
                "quantity": quantity
            })
    
    # Guardar venta
    invoice.save(ignore_permissions=True)
    frappe.db.commit()
    
    return {
        "items_added": items_added,
        "items_skipped": items_skipped,
        "total_items": len(prescription_items)
    }


def validate_all_prescription_items_included(doc, method=None):
    """
    Validar que todos los medicamentos de la receta asociada están incluidos en la venta.
    
    Esta función se ejecuta en validate() de Sales Invoice o POS Invoice.
    
    Args:
        doc: El documento (Sales Invoice o POS Invoice)
        method: El método que dispara el evento (para hooks)
    
    Raises:
        frappe.ValidationError: Si no todos los items de la receta están incluidos
    """
    prescription_name = doc.get("custom_prescription")
    
    if not prescription_name:
        return
    
    if not frappe.db.exists("Prescription", prescription_name):
        return  # Ya se valida en validate_prescription_validity
    
    try:
        prescription = frappe.get_doc("Prescription", prescription_name)
    except frappe.DoesNotExistError:
        return  # Ya se valida en validate_prescription_validity
    
    # Obtener items de la receta
    prescription_item_codes = set()
    for prescription_item in prescription.get("items", []):
        item_code = prescription_item.get("item")
        if item_code:
            prescription_item_codes.add(item_code)
    
    if not prescription_item_codes:
        return  # Receta sin items
    
    # Obtener items de la venta
    invoice_item_codes = set()
    for invoice_item in doc.get("items", []):
        item_code = invoice_item.get("item_code")
        if item_code:
            invoice_item_codes.add(item_code)
    
    # Verificar que todos los items de la receta están en la venta
    missing_items = prescription_item_codes - invoice_item_codes
    
    if missing_items:
        missing_items_list = ", ".join([frappe.bold(item) for item in sorted(missing_items)])
        frappe.throw(
            _("La receta '{0}' incluye medicamentos que no están en esta venta: {1}. Por favor, agregue todos los medicamentos de la receta o quite la asociación de la receta.").format(
                prescription_name,
                missing_items_list
            ),
            title=_("Items de Receta Faltantes")
        )

