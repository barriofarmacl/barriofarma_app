# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Utilidades para auditoría de cambios en control level

Story 1.4: Auditoría de Cambios en Control Level

Este módulo proporciona funciones para detectar y registrar cambios en el
nivel de control (custom_control_level) de medicamentos durante ventas.

FR25: Cambiar control level de medicamento durante venta (con auditoría)
FR40: Registrar cambios en control level con auditoría completa
"""

import frappe
from frappe import _
from frappe.utils import now


def log_control_level_change(
    item_code,
    previous_control_level,
    new_control_level,
    reason,
    changed_by=None,
    reference_doctype=None,
    reference_name=None
):
    """
    Registrar un cambio en control level en el log de auditoría.
    
    Args:
        item_code: Código del item cuyo control level cambió
        previous_control_level: Valor anterior del control level
        new_control_level: Valor nuevo del control level
        reason: Motivo del cambio (obligatorio)
        changed_by: Usuario que realizó el cambio (default: usuario actual)
        reference_doctype: Tipo de documento de referencia (opcional, ej: "Sales Invoice")
        reference_name: Nombre del documento de referencia (opcional)
    
    Returns:
        str: Nombre del registro creado (Control Level Change Log)
    
    Raises:
        frappe.ValidationError: Si el motivo está vacío o el item no existe
    """
    if not reason or not reason.strip():
        frappe.throw(
            _("El motivo del cambio (reason) es obligatorio para registrar cambios en control level. "
              "Debe documentar por qué se cambió el nivel de control del medicamento '{0}'.").format(
                frappe.bold(item_code)
            ),
            title=_("Motivo Requerido para Cambio de Control Level")
        )
    
    if not frappe.db.exists("Item", item_code):
        frappe.throw(
            _("El item '{0}' no existe.").format(frappe.bold(item_code)),
            title=_("Item Inválido")
        )
    
    # Usuario actual si no se especifica
    if not changed_by:
        changed_by = frappe.session.user
    
    # Crear registro de auditoría
    log_doc = frappe.get_doc({
        "doctype": "Control Level Change Log",
        "item_code": item_code,
        "previous_control_level": previous_control_level or "None",
        "new_control_level": new_control_level or "None",
        "changed_by": changed_by,
        "changed_on": now(),
        "reason": reason.strip(),
        "reference_doctype": reference_doctype,
        "reference_name": reference_name
    })
    
    log_doc.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return log_doc.name


def detect_and_log_control_level_changes(doc, items_field="items"):
    """
    Detectar y registrar cambios en control level para items en un documento.
    
    Story 1.4: Auditoría de Cambios en Control Level
    
    Esta función compara el control level actual del Item con el valor especificado
    en el campo custom_new_control_level del item de la venta. Si hay un cambio,
    lo registra en el log de auditoría y actualiza el Item.
    
    FR25: Cambiar control level de medicamento durante venta (con auditoría)
    FR40: Registrar cambios en control level con auditoría completa
    
    Args:
        doc: El documento (Sales Invoice, POS Invoice, etc.)
        items_field: Nombre del campo que contiene los items (default: "items")
    
    Nota:
        Esta función requiere que los items tengan los campos:
        - custom_new_control_level: Nuevo nivel de control (opcional)
        - custom_control_level_change_reason: Motivo del cambio (obligatorio si hay cambio)
        
        Si se especifica un nuevo control level diferente al actual, se debe proporcionar
        un motivo. El cambio se registra en Control Level Change Log y el Item se actualiza.
    """
    if not hasattr(doc, items_field):
        return
    
    items = getattr(doc, items_field, [])
    if not items:
        return
    
    for item in items:
        item_code = item.get("item_code")
        if not item_code:
            continue
        
        # Obtener control level actual del Item
        if not frappe.db.exists("Item", item_code):
            continue
        
        item_doc = frappe.get_doc("Item", item_code)
        current_control_level = item_doc.get("custom_control_level")
        
        # Verificar si hay un campo para nuevo control level en el item de la venta
        new_control_level = item.get("custom_new_control_level")
        change_reason = item.get("custom_control_level_change_reason")
        
        # Solo procesar si hay un nuevo control level especificado y es diferente al actual
        if new_control_level and new_control_level != current_control_level:
            # Validar que el motivo esté presente (ya validado en validate, pero verificar de nuevo)
            if not change_reason or not change_reason.strip():
                frappe.throw(
                    _("El item '{0}' tiene un cambio en control level (de '{1}' a '{2}'), "
                      "pero no se ha especificado el motivo del cambio. "
                      "Debe completar el campo 'Motivo de Cambio de Control Level' "
                      "para poder enviar el documento.").format(
                        frappe.bold(item_code),
                        frappe.bold(current_control_level or "None"),
                        frappe.bold(new_control_level)
                    ),
                    title=_("Motivo Requerido para Cambio de Control Level")
                )
            
            # Registrar el cambio en el log de auditoría
            log_control_level_change(
                item_code=item_code,
                previous_control_level=current_control_level,
                new_control_level=new_control_level,
                reason=change_reason,
                changed_by=frappe.session.user,
                reference_doctype=doc.doctype,
                reference_name=doc.name
            )
            
            # Actualizar el Item con el nuevo control level
            item_doc.custom_control_level = new_control_level
            item_doc.save(ignore_permissions=True)
            frappe.db.commit()
            
            frappe.msgprint(
                _("Se registró el cambio de control level para el item '{0}' (de '{1}' a '{2}') "
                  "en el log de auditoría.").format(
                    frappe.bold(item_code),
                    frappe.bold(current_control_level or "None"),
                    frappe.bold(new_control_level)
                ),
                title=_("Cambio de Control Level Registrado"),
                indicator="blue"
            )


def validate_control_level_change_reason(doc, items_field="items"):
    """
    Validar que si hay cambios en control level, el motivo esté presente.
    
    Story 1.4: Auditoría de Cambios en Control Level
    
    Esta función valida que todos los items con cambios en control level
    tengan un motivo especificado antes de permitir guardar el documento.
    
    FR25: Cambiar control level de medicamento durante venta (con auditoría)
    FR40: Registrar cambios en control level con auditoría completa
    
    Args:
        doc: El documento (Sales Invoice, POS Invoice, etc.)
        items_field: Nombre del campo que contiene los items (default: "items")
    
    Raises:
        frappe.ValidationError: Si hay un cambio en control level sin motivo
    """
    if not hasattr(doc, items_field):
        return
    
    items = getattr(doc, items_field, [])
    if not items:
        return
    
    for item in items:
        item_code = item.get("item_code")
        if not item_code:
            continue
        
        # Obtener control level actual del Item para comparar
        if not frappe.db.exists("Item", item_code):
            continue
        
        item_doc = frappe.get_doc("Item", item_code)
        current_control_level = item_doc.get("custom_control_level")
        
        # Verificar si hay un campo para nuevo control level
        new_control_level = item.get("custom_new_control_level")
        change_reason = item.get("custom_control_level_change_reason")
        
        # Solo validar si hay un nuevo control level especificado Y es diferente al actual
        if new_control_level and new_control_level != current_control_level:
            # Si hay un cambio, el motivo es obligatorio
            if not change_reason or not change_reason.strip():
                frappe.throw(
                    _("El item '{0}' tiene un cambio en control level especificado "
                      "(de '{1}' a '{2}'), pero no se ha proporcionado el motivo del cambio. "
                      "Debe completar el campo 'Motivo de Cambio de Control Level' "
                      "para poder guardar el documento.").format(
                        frappe.bold(item_code),
                        frappe.bold(current_control_level or "None"),
                        frappe.bold(new_control_level)
                    ),
                    title=_("Motivo Requerido para Cambio de Control Level")
                )

