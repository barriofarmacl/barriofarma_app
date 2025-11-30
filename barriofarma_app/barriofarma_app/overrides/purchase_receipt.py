# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Override de Purchase Receipt para validaciones del dominio farmacéutico
Implementación siguiendo workflow *barriofarma-custom-fields
Solo validaciones básicas del dominio en método validate()
"""

import frappe
import json
from frappe import _
from frappe.utils import flt
from datetime import datetime
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
    PurchaseReceipt as ERPNextPurchaseReceipt,
    get_returned_qty_map,
    get_invoiced_qty_map,
)
from erpnext.accounts.party import get_payment_terms_template
from frappe.model.mapper import get_mapped_doc
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
    
    def get_minimum_expiry_months(self, item_code=None):
        """
        Obtener umbral mínimo de vencimiento configurado.
        Prioridad: Item Group > Company > Purchase Receipt > Default (6 meses)
        
        Args:
            item_code: Código del item para obtener umbral desde Item Group
        
        Returns:
            int: Umbral mínimo en meses
        """
        # 1. Si hay umbral configurado directamente en Purchase Receipt, usarlo
        # Nota: Si el valor es el default (6), no lo consideramos como "configurado"
        # para permitir que Item Group/Company tengan prioridad
        pr_threshold = self.get("custom_minimum_expiry_months")
        if pr_threshold and pr_threshold != 6:  # Solo usar si es diferente del default
            return pr_threshold
        
        # 2. Si hay item_code, intentar obtener umbral desde Item Group
        if item_code:
            try:
                item_doc = frappe.get_doc("Item", item_code)
                item_group = item_doc.get("item_group")
                
                if item_group:
                    item_group_doc = frappe.get_doc("Item Group", item_group)
                    item_group_threshold = item_group_doc.get("custom_minimum_expiry_months")
                    # Verificar si el umbral es None o 0 (ambos indican que no está configurado)
                    if item_group_threshold is not None and item_group_threshold != 0:
                        return item_group_threshold
            except (frappe.DoesNotExistError, Exception):
                pass
        
        # 3. Obtener umbral desde Company
        company = self.get("company")
        if company:
            try:
                company_doc = frappe.get_doc("Company", company)
                company_threshold = company_doc.get("custom_minimum_expiry_months")
                if company_threshold:
                    return company_threshold
            except frappe.DoesNotExistError:
                pass
        
        # 4. Default: 6 meses
        return 6
    
    def validate_umbral_vencimiento(self):
        """
        Validar umbral de vencimiento configurable.
        Productos con vencimiento bajo umbral quedan automáticamente en Cuarentena.
        Validación permisiva: ajusta automáticamente el estado QC.
        """
        if not self.get("items"):
            return
        
        for item in self.items:
            if not item.get("batch_no"):
                continue
            
            # Obtener umbral para este item específico (puede variar por Item Group)
            minimum_months = self.get_minimum_expiry_months(item.get("item_code"))
            
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
                else:
                    # Si el vencimiento es mayor o igual al umbral y está en Aceptado,
                    # asegurar que no tenga causa de "Vencimiento corto" (limpiar si fue establecida previamente)
                    current_status = item.get("custom_qc_status") or "Aceptado"
                    if current_status == "Aceptado" and item.get("custom_qc_rejection_reason") == "Vencimiento corto":
                        item.custom_qc_rejection_reason = None
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
    
    def on_submit(self):
        """
        Override: Crear Shelf Movement automáticamente al submitir Purchase Receipt
        si los items tienen custom_to_shelf especificado
        """
        super().on_submit()
        self.create_shelf_movements()
    
    def create_shelf_movements(self):
        """
        Crear registros de Shelf Movement basados en los items del Purchase Receipt
        que tengan custom_to_shelf especificado
        """
        if not self.get("items"):
            return
        
        for item in self.items:
            # Obtener shelf destino desde campo custom
            # Acceder como atributo del child table
            to_shelf = getattr(item, "custom_to_shelf", None) or item.get("custom_to_shelf")
            
            # Solo crear movimiento si hay shelf destino especificado
            if not to_shelf:
                continue
            
            # Purchase Receipt siempre crea movimientos tipo "Recepción"
            movement_type = "Recepción"
            
            # Crear Shelf Movement
            self._create_shelf_movement(
                movement_type=movement_type,
                shelf=to_shelf,
                item=item.item_code,
                quantity=item.qty
            )
    
    def _create_shelf_movement(self, movement_type, shelf, item, quantity, to_shelf=None):
        """
        Crear registro de Shelf Movement
        """
        try:
            movement = frappe.get_doc({
                "doctype": "Shelf Movement",
                "movement_type": movement_type,
                "shelf": shelf,
                "to_shelf": to_shelf,
                "item": item,
                "quantity": quantity,
                "movement_date": self.posting_date or self.transaction_date or datetime.now(),
                "reference_doctype": "Purchase Receipt",
                "reference_name": self.name,
                "notes": f"Movimiento automático desde Purchase Receipt {self.name}"
            })
            
            movement.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(
                message=f"Error al crear Shelf Movement desde Purchase Receipt {self.name}: {str(e)}",
                title="Error en Shelf Movement"
            )
            # No lanzar excepción para no bloquear el submit del Purchase Receipt
            # pero registrar el error para debugging


def make_purchase_invoice(source_name, target_doc=None, args=None):
    """
    Override de make_purchase_invoice para excluir items rechazados/cuarentena
    Solo incluye items con custom_qc_status = "Aceptado"
    """
    if args is None:
        args = {}
    if isinstance(args, str):
        args = json.loads(args)

    doc = frappe.get_doc("Purchase Receipt", source_name)
    returned_qty_map = get_returned_qty_map(source_name)
    invoiced_qty_map = get_invoiced_qty_map(source_name)

    def set_missing_values(source, target):
        if len(target.get("items")) == 0:
            # Verificar si es porque todos están rechazados/cuarentena
            pr_items = source.get("items", [])
            items_aceptados = [item for item in pr_items if (item.get("custom_qc_status") or "Aceptado") == "Aceptado"]
            
            if not items_aceptados:
                frappe.throw(
                    _("No se puede crear Purchase Invoice porque todos los items están Rechazados o en Cuarentena. Solo se pueden facturar items con estado QC 'Aceptado'."),
                    title=_("Sin Items Aceptados")
                )
            else:
                frappe.throw(_("All items have already been Invoiced/Returned"))

        doc = frappe.get_doc(target)
        doc.payment_terms_template = get_payment_terms_template(source.supplier, "Supplier", source.company)
        doc.run_method("onload")
        doc.run_method("set_missing_values")

        if args and args.get("merge_taxes"):
            from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import merge_taxes
            merge_taxes(source.get("taxes") or [], doc)

        doc.run_method("calculate_taxes_and_totals")
        doc.run_method("set_payment_schedule")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty, returned_qty = get_pending_qty(source_doc)
        if frappe.db.get_single_value("Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"):
            target_doc.rejected_qty = 0
        target_doc.stock_qty = flt(target_doc.qty) * flt(
            target_doc.conversion_factor, target_doc.precision("conversion_factor")
        )
        returned_qty_map[source_doc.name] = returned_qty

    def get_pending_qty(item_row):
        qty = item_row.qty
        if frappe.db.get_single_value("Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"):
            qty = item_row.received_qty

        pending_qty = qty - invoiced_qty_map.get(item_row.name, 0)

        if frappe.db.get_single_value("Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"):
            return pending_qty, 0

        returned_qty = flt(returned_qty_map.get(item_row.name, 0))
        if item_row.rejected_qty and returned_qty:
            returned_qty -= item_row.rejected_qty

        if returned_qty:
            if returned_qty >= pending_qty:
                pending_qty = 0
                returned_qty -= pending_qty
            else:
                pending_qty -= returned_qty
                returned_qty = 0

        return pending_qty, returned_qty

    def select_item(d):
        filtered_items = args.get("filtered_children", [])
        child_filter = d.name in filtered_items if filtered_items else True
        return child_filter
    
    def filter_qc_accepted_items(item_row):
        """
        Filtro adicional: excluir items con custom_qc_status != "Aceptado"
        Invariante: No pagar rechazados/cuarentena
        Nota: En get_mapped_doc, si el filtro retorna True, el item se EXCLUYE (continue)
        """
        # Obtener el estado QC del item
        qc_status = item_row.get("custom_qc_status") or "Aceptado"
        
        # Excluir si NO está Aceptado (invariante: no pagar rechazados/cuarentena)
        # Retornar True para excluir el item
        if qc_status != "Aceptado":
            return True
        
        # Aplicar el filtro original de ERPNext
        # El filtro original retorna True para EXCLUIR si:
        # - No es return: excluir si pending_qty <= 0 (incluir solo si pending_qty > 0)
        # - Es return: excluir si pending_qty > 0 (incluir solo si pending_qty <= 0)
        pending_qty, _ = get_pending_qty(item_row)
        if not doc.get("is_return"):
            # Para Purchase Receipt normal: excluir si no hay cantidad pendiente
            return pending_qty <= 0
        else:
            # Para Purchase Return: excluir si hay cantidad pendiente
            return pending_qty > 0

    doclist = get_mapped_doc(
        "Purchase Receipt",
        source_name,
        {
            "Purchase Receipt": {
                "doctype": "Purchase Invoice",
                "field_map": {
                    "supplier_warehouse": "supplier_warehouse",
                    "is_return": "is_return",
                    "bill_date": "bill_date",
                },
                "validation": {
                    "docstatus": ["=", 1],
                },
            },
            "Purchase Receipt Item": {
                "doctype": "Purchase Invoice Item",
                "field_map": {
                    "name": "pr_detail",
                    "parent": "purchase_receipt",
                    "qty": "received_qty",
                    "purchase_order_item": "po_detail",
                    "purchase_order": "purchase_order",
                    "is_fixed_asset": "is_fixed_asset",
                    "asset_location": "asset_location",
                    "asset_category": "asset_category",
                    "wip_composite_asset": "wip_composite_asset",
                },
                "postprocess": update_item,
                "filter": filter_qc_accepted_items,
                "condition": select_item,
            },
            "Purchase Taxes and Charges": {
                "doctype": "Purchase Taxes and Charges",
                "reset_value": not (args and args.get("merge_taxes")),
                "ignore": args.get("merge_taxes") if args else 0,
            },
        },
        target_doc,
        set_missing_values,
    )

    return doclist
