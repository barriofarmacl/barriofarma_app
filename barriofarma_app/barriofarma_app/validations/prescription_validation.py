# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Validación de vigencia de receta médica para ventas (Sales Invoice y POS Invoice)

Story 5.2: Validación de Vigencia de Receta

Esta validación asegura que las recetas asociadas a ventas estén vigentes y no hayan
excedido el límite de dispensaciones.
"""

import frappe
from frappe import _
from frappe.utils import getdate, today
from barriofarma_app.barriofarma_app.utils.prescription_items import validate_all_prescription_items_included


def validate_prescription_validity(doc, method=None):
    """
    Validar que la receta asociada a la venta esté vigente y no haya excedido límites.
    
    Esta función se ejecuta cuando Sales Invoice o POS Invoice tiene una receta asociada.
    
    Args:
        doc: El documento (Sales Invoice o POS Invoice)
        method: El método que dispara el evento (para hooks)
    
    Raises:
        frappe.ValidationError: Si la receta no es válida
    """
    # Obtener receta asociada (puede ser un campo custom o desde items)
    prescription_name = doc.get("custom_prescription")
    
    # Story 4.2: Si no hay receta asociada, verificar si hay items que requieren receta
    if not prescription_name:
        # Buscar items que requieren receta
        items_requiring_prescription = []
        for item in doc.get("items", []):
            if item.item_code:
                try:
                    item_doc = frappe.get_doc("Item", item.item_code)
                    if item_doc.get("custom_requires_prescription_retention"):
                        items_requiring_prescription.append(item.item_code)
                except frappe.DoesNotExistError:
                    continue
        
        # Si hay items que requieren receta pero no hay receta asociada, lanzar error
        if items_requiring_prescription:
            items_list = ", ".join([frappe.bold(item) for item in items_requiring_prescription])
            frappe.throw(
                _("Esta venta incluye productos que requieren receta médica: {0}. Por favor, asocie una receta válida en el campo 'Receta Médica'.").format(
                    items_list
                ),
                title=_("Receta Requerida")
            )
        
        # Si no hay items que requieran receta, no validar
        return
    
    # Validar que la receta existe
    if not frappe.db.exists("Prescription", prescription_name):
        frappe.throw(
            _("La receta '{0}' no existe.").format(prescription_name),
            title=_("Receta No Encontrada")
        )
    
    # Obtener datos de la receta
    try:
        prescription = frappe.get_doc("Prescription", prescription_name)
    except (frappe.DoesNotExistError, Exception):
        frappe.throw(
            _("La receta '{0}' no existe.").format(prescription_name),
            title=_("Receta No Encontrada")
        )
    
    # Validar que la receta no está vencida
    if prescription.get("valid_till"):
        valid_till = getdate(prescription.valid_till)
        current_date = getdate(today())
        
        if valid_till < current_date:
            frappe.throw(
                _("La receta '{0}' está vencida (válida hasta {1}). No se puede usar para dispensar medicamentos.").format(
                    prescription_name,
                    valid_till.strftime("%d/%m/%Y")
                ),
                title=_("Receta Vencida")
            )
    
    # Validar que la receta no ha excedido max_dispensations
    max_dispensations = prescription.get("max_dispensations") or 0
    dispensation_count = prescription.get("dispensation_count") or 0
    
    if dispensation_count >= max_dispensations:
        frappe.throw(
            _("La receta '{0}' ha alcanzado el límite máximo de dispensaciones ({1}/{2}). No se puede usar para dispensar más medicamentos.").format(
                prescription_name,
                dispensation_count,
                max_dispensations
            ),
            title=_("Límite de Dispensaciones Alcanzado")
        )
    
    # Validar que la receta está en estado válido
    status = prescription.get("status")
    invalid_statuses = ["Vencida"]
    
    if status in invalid_statuses:
        frappe.throw(
            _("La receta '{0}' está en estado '{1}' y no puede ser usada para dispensar medicamentos.").format(
                prescription_name,
                status
            ),
            title=_("Estado de Receta Inválido")
        )
    
    # Story 5.3: Validar que todos los items de la receta están incluidos en la venta
    validate_all_prescription_items_included(doc, method)


def update_prescription_dispensation(doc, method=None):
    """
    Actualizar dispensation_count de la receta y crear registro en Prescription Sales Invoice
    cuando se confirma una venta.
    
    Esta función se ejecuta en on_submit de Sales Invoice o POS Invoice.
    
    Args:
        doc: El documento (Sales Invoice o POS Invoice)
        method: El método que dispara el evento (para hooks)
    """
    prescription_name = doc.get("custom_prescription")
    
    if not prescription_name:
        return
    
    if not frappe.db.exists("Prescription", prescription_name):
        frappe.log_error(
            message=f"Receta {prescription_name} no encontrada al actualizar dispensación desde {doc.doctype} {doc.name}",
            title="Error al Actualizar Dispensación"
        )
        return
    
    try:
        # Obtener receta
        prescription = frappe.get_doc("Prescription", prescription_name)
        
        # Incrementar dispensation_count
        current_count = prescription.get("dispensation_count") or 0
        prescription.dispensation_count = current_count + 1
        
        # Actualizar estado si es necesario
        prescription.update_status()
        
        # Guardar receta
        prescription.save(ignore_permissions=True)
        
        # Crear registro en Prescription Sales Invoice
        prescription_sales_invoice = {
            "doctype": "Prescription Sales Invoice",
            "sales_invoice": doc.name,
            "date": doc.posting_date or today(),
            "dispensed_by": frappe.session.user,
            "notes": f"Dispensación desde {doc.doctype} {doc.name}"
        }
        
        # Agregar a la tabla related_sales_invoices de la receta
        prescription.append("related_sales_invoices", prescription_sales_invoice)
        prescription.save(ignore_permissions=True)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(
            message=f"Error al actualizar dispensación de receta {prescription_name} desde {doc.doctype} {doc.name}: {frappe.get_traceback()}",
            title="Error al Actualizar Dispensación"
        )
        # No lanzar excepción para no bloquear el submit, pero registrar el error
        frappe.db.rollback()

