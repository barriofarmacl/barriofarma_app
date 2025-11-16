# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Override de Purchase Receipt para validaciones del dominio farmacéutico
Implementación siguiendo workflow *barriofarma-custom-fields
Solo validaciones básicas del dominio en método validate()
"""

import frappe
from frappe import _
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt as ERPNextPurchaseReceipt
from frappe.utils import getdate, today


class PurchaseReceipt(ERPNextPurchaseReceipt):
    """
    Override de Purchase Receipt con validaciones farmacéuticas
    """
    
    def validate(self):
        """Validar invariantes del dominio antes de guardar"""
        super().validate()
        self.validate_items_requieren_lote_si_necesario()
        self.validate_controlados_requieren_lote_vencimiento()
        self.validate_qc_rejection_reason_required()
        self.validate_umbral_vencimiento()
        self.validate_sobrante_no_disponible()
    
    def validate_items_requieren_lote_si_necesario(self):
        """
        Validar que items con has_batch_no=1 tengan batch_no asignado
        Validación estricta: lanza error si falta lote
        """
        if not self.get("items"):
            return
        
        for item in self.items:
            item_doc = frappe.get_doc("Item", item.item_code)
            if item_doc.get("has_batch_no") and not item.get("batch_no"):
                frappe.throw(
                    _("El ítem '{0}' requiere gestión por lote. Debe asignar un lote en la línea de recepción.").format(
                        frappe.bold(item.item_code)
                    ),
                    title=_("Lote Requerido")
                )
    
    def validate_controlados_requieren_lote_vencimiento(self):
        """
        Invariante: Productos controlados (Psicotrópico/Estupefaciente) siempre requieren
        lote y vencimiento en Purchase Receipt
        Validación estricta: lanza error si falta lote o vencimiento
        """
        if not self.get("items"):
            return
        
        for item in self.items:
            item_doc = frappe.get_doc("Item", item.item_code)
            control_level = item_doc.get("custom_control_level")
            
            if control_level in ("Psicotrópico", "Estupefaciente"):
                # Validar que tiene lote
                if not item.get("batch_no"):
                    frappe.throw(
                        _("Los medicamentos {0} requieren gestión por lote. El ítem '{1}' debe tener un lote asignado.").format(
                            frappe.bold(control_level),
                            frappe.bold(item.item_code)
                        ),
                        title=_("Invariante de Control No Cumplida")
                    )
                
                # Validar que el batch tiene fecha de vencimiento
                if item.get("batch_no"):
                    batch = frappe.get_doc("Batch", item.batch_no)
                    if not batch.get("expiry_date"):
                        frappe.throw(
                            _("El lote '{0}' del medicamento controlado '{1}' debe tener fecha de vencimiento.").format(
                                frappe.bold(item.batch_no),
                                frappe.bold(item.item_code)
                            ),
                            title=_("Fecha de Vencimiento Requerida")
                        )
    
    def validate_qc_rejection_reason_required(self):
        """
        Validar que si estado QC es Rechazado o Cuarentena, debe tener causa
        Validación estricta: lanza error si falta causa
        """
        if not self.get("items"):
            return
        
        for item in self.items:
            qc_status = item.get("custom_qc_status") or "Aceptado"
            rejection_reason = item.get("custom_qc_rejection_reason")
            
            if qc_status in ("Rechazado", "Cuarentena") and not rejection_reason:
                frappe.throw(
                    _("El ítem '{0}' tiene estado QC '{1}' pero no tiene causa especificada. Debe indicar la razón del rechazo o cuarentena.").format(
                        frappe.bold(item.item_code),
                        frappe.bold(qc_status)
                    ),
                    title=_("Causa de Rechazo/Cuarentena Requerida")
                )
    
    def validate_umbral_vencimiento(self):
        """
        Validar umbral de vencimiento configurable.
        Productos con vencimiento bajo umbral quedan automáticamente en Cuarentena.
        Validación permisiva: ajusta automáticamente el estado QC.
        """
        if not self.get("items"):
            return
        
        # Obtener umbral configurado (default: 6 meses)
        minimum_months = self.get("custom_minimum_expiry_months") or 6
        
        for item in self.items:
            if not item.get("batch_no"):
                continue
            
            try:
                batch = frappe.get_doc("Batch", item.batch_no)
                expiry_date = batch.get("expiry_date")
                
                if not expiry_date:
                    continue
                
                expiry_date_obj = getdate(expiry_date)
                today_obj = getdate(today())
                months_until_expiry = (expiry_date_obj.year - today_obj.year) * 12 + (expiry_date_obj.month - today_obj.month)
                
                # Si el vencimiento es menor al umbral, marcar como Cuarentena automáticamente
                if months_until_expiry < minimum_months:
                    current_status = item.get("custom_qc_status") or "Aceptado"
                    
                    # Solo cambiar si está en Aceptado (no sobrescribir decisiones manuales)
                    if current_status == "Aceptado":
                        item.custom_qc_status = "Cuarentena"
                        if not item.get("custom_qc_rejection_reason"):
                            item.custom_qc_rejection_reason = "Vencimiento corto"
            except frappe.DoesNotExistError:
                # Batch no existe aún, se validará después
                pass
    
    def validate_sobrante_no_disponible(self):
        """
        Invariante: Sobrante no autorizado nunca queda disponible para venta hasta decisión administrativa.
        Validación permisiva: ajusta automáticamente el estado QC a Cuarentena.
        """
        if not self.get("items"):
            return
        
        for item in self.items:
            if item.get("custom_is_excess"):
                # Si es sobrante, debe estar en estado que no permita venta
                qc_status = item.get("custom_qc_status") or "Aceptado"
                if qc_status == "Aceptado":
                    # Sobrante no puede estar Aceptado directamente
                    item.custom_qc_status = "Cuarentena"
                    if not item.get("custom_qc_rejection_reason"):
                        item.custom_qc_rejection_reason = "Sobrante no autorizado"
