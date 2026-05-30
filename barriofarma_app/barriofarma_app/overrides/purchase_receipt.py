# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Override de Purchase Receipt para validaciones del dominio farmacéutico

Story 1.2: Refinamiento de Validaciones de Purchase Receipt

Este módulo implementa las invariantes DDD del dominio farmacéutico para Purchase Receipt:
- FR16: Registrar lotes y fechas de caducidad durante recepción
- FR17: Realizar control de calidad básico durante recepción
- FR24: Validar que medicamentos controlados tengan receta (validación de lote/vencimiento)

Invariantes implementadas:
1. Items con has_batch_no=1 deben tener batch_no asignado
2. Productos controlados (Psicotrópico/Estupefaciente) requieren lote y vencimiento
3. Estado QC Rechazado/Cuarentena requiere causa (custom_qc_rejection_reason)
4. Sublotes bajo umbral de vencimiento deben ir a cuarentena automáticamente
5. Sobrantes no pueden estar disponibles (se ajustan automáticamente a Cuarentena)
"""

import frappe
import json
from frappe import _
from frappe.utils import flt
from barriofarma_app.barriofarma_app.utils.shelf_movement_submit import insert_and_submit_shelf_movement
from barriofarma_app.barriofarma_app.utils.shelf_validations import validate_inbound_shelf_line
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
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from erpnext.accounts.doctype.pricing_rule_detail.pricing_rule_detail import PricingRuleDetail
        from erpnext.accounts.doctype.purchase_taxes_and_charges.purchase_taxes_and_charges import PurchaseTaxesandCharges
        from erpnext.buying.doctype.purchase_receipt_item_supplied.purchase_receipt_item_supplied import PurchaseReceiptItemSupplied
        from erpnext.stock.doctype.purchase_receipt_item.purchase_receipt_item import PurchaseReceiptItem
        from frappe.types import DF

        additional_discount_percentage: DF.Float
        address_display: DF.SmallText | None
        amended_from: DF.Link | None
        apply_discount_on: DF.Literal["", "Grand Total", "Net Total"]
        apply_putaway_rule: DF.Check
        auto_repeat: DF.Link | None
        base_discount_amount: DF.Currency
        base_grand_total: DF.Currency
        base_in_words: DF.Data | None
        base_net_total: DF.Currency
        base_rounded_total: DF.Currency
        base_rounding_adjustment: DF.Currency
        base_tax_withholding_net_total: DF.Currency
        base_taxes_and_charges_added: DF.Currency
        base_taxes_and_charges_deducted: DF.Currency
        base_total: DF.Currency
        base_total_taxes_and_charges: DF.Currency
        billing_address: DF.Link | None
        billing_address_display: DF.SmallText | None
        buying_price_list: DF.Link | None
        company: DF.Link
        contact_display: DF.SmallText | None
        contact_email: DF.SmallText | None
        contact_mobile: DF.SmallText | None
        contact_person: DF.Link | None
        conversion_rate: DF.Float
        cost_center: DF.Link | None
        currency: DF.Link
        disable_rounded_total: DF.Check
        discount_amount: DF.Currency
        dispatch_address: DF.Link | None
        dispatch_address_display: DF.TextEditor | None
        grand_total: DF.Currency
        group_same_items: DF.Check
        ignore_pricing_rule: DF.Check
        in_words: DF.Data | None
        incoterm: DF.Link | None
        instructions: DF.SmallText | None
        inter_company_reference: DF.Link | None
        is_internal_supplier: DF.Check
        is_old_subcontracting_flow: DF.Check
        is_return: DF.Check
        is_subcontracted: DF.Check
        items: DF.Table[PurchaseReceiptItem]
        language: DF.Data | None
        letter_head: DF.Link | None
        lr_date: DF.Date | None
        lr_no: DF.Data | None
        named_place: DF.Data | None
        naming_series: DF.Literal["MAT-PRE-.YYYY.-", "MAT-PR-RET-.YYYY.-"]
        net_total: DF.Currency
        other_charges_calculation: DF.TextEditor | None
        per_billed: DF.Percent
        per_returned: DF.Percent
        plc_conversion_rate: DF.Float
        posting_date: DF.Date
        posting_time: DF.Time
        price_list_currency: DF.Link | None
        pricing_rules: DF.Table[PricingRuleDetail]
        project: DF.Link | None
        range: DF.Data | None
        rejected_warehouse: DF.Link | None
        remarks: DF.SmallText | None
        represents_company: DF.Link | None
        return_against: DF.Link | None
        rounded_total: DF.Currency
        rounding_adjustment: DF.Currency
        scan_barcode: DF.Data | None
        select_print_heading: DF.Link | None
        set_from_warehouse: DF.Link | None
        set_posting_time: DF.Check
        set_warehouse: DF.Link | None
        shipping_address: DF.Link | None
        shipping_address_display: DF.SmallText | None
        shipping_rule: DF.Link | None
        status: DF.Literal["", "Draft", "Partly Billed", "To Bill", "Completed", "Return", "Return Issued", "Cancelled", "Closed"]
        subcontracting_receipt: DF.Link | None
        supplied_items: DF.Table[PurchaseReceiptItemSupplied]
        supplier: DF.Link
        supplier_address: DF.Link | None
        supplier_delivery_note: DF.Data | None
        supplier_name: DF.Data | None
        supplier_warehouse: DF.Link | None
        tax_category: DF.Link | None
        tax_withholding_net_total: DF.Currency
        taxes: DF.Table[PurchaseTaxesandCharges]
        taxes_and_charges: DF.Link | None
        taxes_and_charges_added: DF.Currency
        taxes_and_charges_deducted: DF.Currency
        tc_name: DF.Link | None
        terms: DF.TextEditor | None
        title: DF.Data | None
        total: DF.Currency
        total_net_weight: DF.Float
        total_qty: DF.Float
        total_taxes_and_charges: DF.Currency
        transporter_name: DF.Data | None
    # end: auto-generated types
    """
    Override de Purchase Receipt con validaciones farmacéuticas
    """

    def before_validate(self):
        super().before_validate()
        self._align_currency_with_purchase_order_or_company()

    def _align_currency_with_purchase_order_or_company(self):
        """ERPNext v16 exige que PR.currency coincida con la PO referenciada."""
        purchase_orders = {
            item.get("purchase_order") for item in self.items if item.get("purchase_order")
        }
        if len(purchase_orders) == 1:
            po = frappe.db.get_value(
                "Purchase Order",
                purchase_orders.pop(),
                ["currency", "conversion_rate"],
                as_dict=True,
            )
            if po and po.currency:
                self.currency = po.currency
                self.conversion_rate = po.conversion_rate or 1
                return

        if self.company:
            company_currency = frappe.db.get_value("Company", self.company, "default_currency")
            if company_currency:
                self.currency = company_currency
                self.conversion_rate = 1
    
    def validate(self):
        """
        Validar invariantes del dominio farmacéutico antes de guardar Purchase Receipt.
        
        Este método ejecuta todas las validaciones DDD en el orden correcto:
        1. Validación contra Purchase Order (si existe)
        2. Validación de lotes requeridos (items con has_batch_no=1)
        3. Validación de productos controlados (lote y vencimiento obligatorios)
        4. Validación de causa para estados QC Rechazado/Cuarentena
        5. Validación de umbral de vencimiento (ajuste automático a Cuarentena)
        6. Validación de sobrantes (ajuste automático a Cuarentena)
        
        Todas las validaciones se ejecutan antes de permitir guardar el documento.
        """
        super().validate()
        self.validate_against_purchase_order()
        self.auto_create_batches_if_needed()  # Story 3.2: Crear Batch automáticamente si no existe
        self.validate_items_requieren_lote_si_necesario()
        self.validate_controlados_requieren_lote_vencimiento()
        self.validate_qc_rejection_reason_required()
        self.validate_umbral_vencimiento()
        self.validate_sobrante_no_disponible()
        self.validate_shelf_required()
    
    def validate_shelf_required(self):
        """Issue #58: toda recepción debe indicar estante destino por línea."""
        if not self.get("items"):
            return

        for item in self.items:
            if not flt(item.qty):
                continue

            line_wh = item.warehouse or self.set_warehouse
            to_shelf = getattr(item, "custom_to_shelf", None) or item.get("custom_to_shelf")
            from barriofarma_app.barriofarma_app.utils.shelf_validations import resolve_shelf_for_warehouse

            to_shelf = resolve_shelf_for_warehouse(line_wh, to_shelf)
            if to_shelf and to_shelf != item.get("custom_to_shelf"):
                item.custom_to_shelf = to_shelf
            validate_inbound_shelf_line(
                item.idx,
                item.item_code,
                line_wh,
                to_shelf,
                field_label=_("Estante destino"),
                missing_shelf_message=_(
                    "Fila #{0}: debe indicar el <strong>Estante Destino</strong> para el producto "
                    "{1} en el almacén {2}."
                ).format(
                    item.idx,
                    frappe.bold(item.item_code),
                    frappe.bold(line_wh or "-"),
                ),
            )

    def auto_create_batches_if_needed(self):
        """
        Crear Batch automáticamente si no existe cuando se ingresa batch_no en items.
        
        Story 3.2: Optimización de Registro de Lotes durante Recepción
        
        FR16: Registrar lotes y fechas de caducidad durante recepción
        
        Esta función permite que el usuario ingrese un batch_id directamente en el campo
        batch_no del Purchase Receipt Item, y si el Batch no existe, se crea automáticamente.
        Esto optimiza el proceso de recepción al evitar tener que crear Batch manualmente
        antes de recibir productos.
        
        La creación automática requiere:
        - Item debe tener has_batch_no=1
        - batch_no debe estar especificado en el item
        - Si el item tiene expiry_date en el row, se usa para el Batch
        - Si no, se puede crear sin expiry_date (se validará después)
        
        Nota: Esta función se ejecuta antes de las validaciones para que los Batch
        estén disponibles cuando se validen los items.
        """
        if not self.get("items"):
            return
        
        for item in self.items:
            if not item.item_code:
                continue
            
            # Verificar si el item requiere batch
            try:
                item_doc = frappe.get_doc("Item", item.item_code)
                if not item_doc.get("has_batch_no"):
                    continue
            except frappe.DoesNotExistError:
                continue
            
            # Si hay batch_no especificado pero el Batch no existe, crearlo
            batch_no = item.get("batch_no")
            if batch_no:
                # Verificar si el Batch existe
                if not frappe.db.exists("Batch", batch_no):
                    # Crear Batch automáticamente
                    try:
                        # Intentar obtener expiry_date si el Batch ya existe con otro nombre
                        # o si hay un campo custom en el item (futuro)
                        expiry_date = None
                        if hasattr(item, 'expiry_date') and item.expiry_date:
                            expiry_date = item.expiry_date
                        
                        batch_doc = frappe.get_doc({
                            "doctype": "Batch",
                            "batch_id": batch_no,
                            "item": item.item_code
                        })
                        
                        if expiry_date:
                            batch_doc.expiry_date = expiry_date
                        
                        batch_doc.insert(ignore_permissions=True)
                        frappe.db.commit()
                        
                        # Mensaje solo en modo desarrollo o si está habilitado
                        if frappe.conf.developer_mode or frappe.db.get_single_value("System Settings", "enable_batch_auto_creation_message"):
                            frappe.msgprint(
                                _("Batch '{0}' creado automáticamente para el item '{1}'.").format(
                                    frappe.bold(batch_no),
                                    frappe.bold(item.item_code)
                                ),
                                indicator="blue",
                                title=_("Batch Creado Automáticamente")
                            )
                    except Exception as e:
                        frappe.log_error(
                            message=f"Error al crear Batch automáticamente {batch_no} para item {item.item_code}: {str(e)}",
                            title="Error en Creación Automática de Batch"
                        )
                        # No lanzar error, solo registrar para debugging
                        # El usuario puede crear el Batch manualmente si es necesario
    
    def validate_against_purchase_order(self):
        """
        Validar recepción contra Purchase Order si existe.
        
        FR14: Recibir productos contra orden de compra
        FR15: Validar recepción contra documento de entrega del proveedor
        
        Esta validación compara los items del Purchase Receipt con los items del
        Purchase Order para detectar discrepancias en:
        - Cantidades recibidas vs ordenadas
        - Productos recibidos vs ordenados
        - Precios (si aplica) vs precios en Purchase Order
        
        Validación permisiva: muestra advertencias para diferencias menores,
        errores solo para discrepancias críticas (productos no ordenados).
        Permite recepción parcial con justificación.
        
        Raises:
            frappe.ValidationError: Si hay productos recibidos que no están en Purchase Order
        """
        purchase_order = self.get("purchase_order")
        if not purchase_order:
            purchase_orders = {
                item.get("purchase_order") for item in self.items if item.get("purchase_order")
            }
            if len(purchase_orders) == 1:
                purchase_order = purchase_orders.pop()

        if not purchase_order:
            # No hay Purchase Order en cabecera ni líneas, no validar
            return
        
        if not self.get("items"):
            return
        
        try:
            po = frappe.get_doc("Purchase Order", purchase_order)
        except frappe.DoesNotExistError:
            frappe.msgprint(
                _("Purchase Order {0} no existe. La validación contra Purchase Order se omitirá.").format(
                    frappe.bold(purchase_order)
                ),
                indicator="orange",
                title=_("Purchase Order No Encontrado")
            )
            return
        
        # Verificar que Purchase Order esté en estado válido
        if po.docstatus != 1:  # No está submitted
            frappe.msgprint(
                _("Purchase Order {0} no está en estado válido (docstatus={1}). "
                  "Solo se pueden recibir productos contra Purchase Orders confirmados.").format(
                    frappe.bold(purchase_order),
                    po.docstatus
                ),
                indicator="orange",
                title=_("Purchase Order No Confirmado")
            )
            return
        
        # Crear mapa de items del Purchase Order por item_code
        po_items_map = {}
        for po_item in po.items:
            item_code = po_item.item_code
            if item_code not in po_items_map:
                po_items_map[item_code] = []
            po_items_map[item_code].append({
                "name": po_item.name,
                "item_code": po_item.item_code,
                "item_name": po_item.item_name,
                "qty": po_item.qty,
                "rate": po_item.rate,
                "received_qty": po_item.received_qty or 0,
                "pending_qty": po_item.qty - (po_item.received_qty or 0)
            })
        
        # Validar items del Purchase Receipt
        warnings = []
        errors = []
        
        for pr_item in self.items:
            item_code = pr_item.item_code
            pr_qty = pr_item.qty
            pr_rate = pr_item.rate
            
            if item_code not in po_items_map:
                # Producto recibido que no está en Purchase Order
                errors.append(
                    _("El producto '{0}' está en la recepción pero no está en el Purchase Order {1}. "
                      "Solo se pueden recibir productos que estén en la orden de compra.").format(
                        frappe.bold(item_code),
                        frappe.bold(self.purchase_order)
                    )
                )
                continue
            
            # Encontrar el item del PO que corresponde (puede haber múltiples líneas)
            po_item_matched = None
            for po_item in po_items_map[item_code]:
                # Si hay purchase_order_item link, usar ese
                if pr_item.get("purchase_order_item") == po_item["name"]:
                    po_item_matched = po_item
                    break
                # Si no hay link, usar el primero con pending_qty > 0
                elif po_item["pending_qty"] > 0:
                    if po_item_matched is None or po_item_matched["pending_qty"] < po_item["pending_qty"]:
                        po_item_matched = po_item
            
            if not po_item_matched:
                # Todos los items del PO para este producto ya fueron recibidos
                warnings.append(
                    _("El producto '{0}' ya fue completamente recibido en el Purchase Order {1}. "
                      "Cantidad recibida: {2}").format(
                        frappe.bold(item_code),
                        frappe.bold(self.purchase_order),
                        pr_qty
                    )
                )
                continue
            
            po_qty = po_item_matched["qty"]
            po_rate = po_item_matched["rate"]
            po_received_qty = po_item_matched["received_qty"]
            po_pending_qty = po_item_matched["pending_qty"]
            
            # Validar cantidad
            if pr_qty > po_pending_qty:
                # Sobrante: cantidad recibida mayor a pendiente
                excess_qty = pr_qty - po_pending_qty
                warnings.append(
                    _("El producto '{0}' tiene sobrante de {1} unidades. "
                      "Ordenado: {2}, Ya recibido: {3}, Pendiente: {4}, Recibido: {5}. "
                      "El sobrante será marcado automáticamente como 'Sobrante'.").format(
                        frappe.bold(item_code),
                        frappe.bold(excess_qty),
                        po_qty,
                        po_received_qty,
                        po_pending_qty,
                        pr_qty
                    )
                )
                # Marcar como sobrante si la cantidad recibida es mayor a la pendiente
                if pr_qty > po_pending_qty:
                    pr_item.custom_is_excess = 1
            elif pr_qty < po_pending_qty:
                # Faltante: cantidad recibida menor a pendiente (recepción parcial)
                short_qty = po_pending_qty - pr_qty
                warnings.append(
                    _("El producto '{0}' tiene recepción parcial. "
                      "Pendiente: {1}, Recibido: {2}, Faltante: {3}. "
                      "Esto es válido si es una recepción parcial.").format(
                        frappe.bold(item_code),
                        po_pending_qty,
                        pr_qty,
                        short_qty
                    )
                )
            
            # Validar precio (solo advertencia, no error)
            if pr_rate and po_rate and abs(flt(pr_rate) - flt(po_rate)) > 0.01:
                price_diff = abs(flt(pr_rate) - flt(po_rate))
                warnings.append(
                    _("El producto '{0}' tiene diferencia de precio. "
                      "Precio en PO: {1}, Precio en recepción: {2}, Diferencia: {3}").format(
                        frappe.bold(item_code),
                        frappe.bold(frappe.format_value(po_rate, {"fieldtype": "Currency"})),
                        frappe.bold(frappe.format_value(pr_rate, {"fieldtype": "Currency"})),
                        frappe.bold(frappe.format_value(price_diff, {"fieldtype": "Currency"}))
                    )
                )
        
        # Mostrar errores (bloquean guardado)
        if errors:
            frappe.throw(
                _("Errores de validación contra Purchase Order {0}:\n\n{1}").format(
                    frappe.bold(purchase_order),
                    "\n".join(f"• {e}" for e in errors)
                ),
                title=_("Validación contra Purchase Order - Errores")
            )
        
        # Mostrar advertencias (no bloquean, solo informan)
        if warnings:
            frappe.msgprint(
                _("Advertencias de validación contra Purchase Order {0}:\n\n{1}").format(
                    frappe.bold(purchase_order),
                    "\n".join(f"• {w}" for w in warnings)
                ),
                indicator="orange",
                title=_("Validación contra Purchase Order - Advertencias")
            )
    
    def validate_items_requieren_lote_si_necesario(self):
        """
        Invariante DDD: Items con has_batch_no=1 deben tener batch_no asignado.
        
        FR16: Registrar lotes durante recepción
        
        Esta validación asegura que todos los items que requieren gestión por lote
        tengan un lote asignado en la recepción. Sin lote, no se puede rastrear
        la trazabilidad del medicamento.
        
        Validación estricta: lanza error si falta lote (no permite guardar).
        
        Raises:
            frappe.ValidationError: Si un item con has_batch_no=1 no tiene batch_no asignado
        """
        if not self.get("items"):
            return
        
        for item in self.items:
            item_doc = frappe.get_doc("Item", item.item_code)
            if item_doc.get("has_batch_no") and not item.get("batch_no"):
                frappe.throw(
                    _("El ítem '{0}' requiere gestión por lote según su configuración (has_batch_no=1). "
                      "Debe asignar un lote en la línea de recepción para poder guardar el documento. "
                      "Si el lote no existe, créelo primero desde el DocType Batch.").format(
                        frappe.bold(item.item_code)
                    ),
                    title=_("Lote Requerido - No se puede guardar sin lote")
                )
    
    def validate_controlados_requieren_lote_vencimiento(self):
        """
        Invariante DDD: Productos controlados siempre requieren lote y vencimiento.
        
        FR16: Registrar lotes y fechas de caducidad durante recepción
        FR24: Validar que medicamentos controlados tengan receta (validación de trazabilidad)
        
        Los medicamentos controlados (Psicotrópico/Estupefaciente) requieren trazabilidad
        completa según normativa farmacéutica chilena. Esta validación asegura que:
        1. Todos los productos controlados tengan lote asignado
        2. Todos los lotes de productos controlados tengan fecha de vencimiento
        
        Sin estas validaciones, no se puede garantizar la trazabilidad completa requerida
        por la normativa.
        
        Validación estricta: lanza error si falta lote o vencimiento (no permite guardar).
        
        Raises:
            frappe.ValidationError: Si un producto controlado no tiene lote o el lote no tiene fecha de vencimiento
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
                        _("Los medicamentos {0} requieren gestión por lote según normativa farmacéutica chilena. "
                          "El ítem '{1}' debe tener un lote asignado en la línea de recepción. "
                          "Si el lote no existe, créelo primero desde el DocType Batch.").format(
                            frappe.bold(control_level),
                            frappe.bold(item.item_code)
                        ),
                        title=_("Invariante de Control No Cumplida - Lote Requerido")
                    )
                
                # Validar que el batch tiene fecha de vencimiento
                if item.get("batch_no"):
                    batch = frappe.get_doc("Batch", item.batch_no)
                    if not batch.get("expiry_date"):
                        frappe.throw(
                            _("El lote '{0}' del medicamento controlado '{1}' (nivel de control: {2}) "
                              "debe tener fecha de vencimiento configurada. "
                              "Edite el lote '{0}' y agregue la fecha de vencimiento (expiry_date).").format(
                                frappe.bold(item.batch_no),
                                frappe.bold(item.item_code),
                                frappe.bold(control_level)
                            ),
                            title=_("Fecha de Vencimiento Requerida - Producto Controlado")
                        )
    
    def validate_qc_rejection_reason_required(self):
        """
        Invariante DDD: Estado QC Rechazado/Cuarentena requiere causa documentada.
        
        FR17: Realizar control de calidad básico durante recepción
        
        Cuando un producto es rechazado o puesto en cuarentena durante la recepción,
        es crítico documentar la razón para:
        - Auditoría y cumplimiento normativo
        - Trazabilidad de decisiones de calidad
        - Análisis de problemas recurrentes con proveedores
        
        Esta validación asegura que todas las decisiones de rechazo/cuarentena
        estén documentadas con una causa clara.
        
        Validación estricta: lanza error si falta causa (no permite guardar).
        
        Raises:
            frappe.ValidationError: Si un item con estado QC Rechazado/Cuarentena no tiene causa especificada
        """
        if not self.get("items"):
            return
        
        for item in self.items:
            qc_status = item.get("custom_qc_status") or "Aceptado"
            rejection_reason = item.get("custom_qc_rejection_reason")
            
            if qc_status in ("Rechazado", "Cuarentena") and not rejection_reason:
                frappe.throw(
                    _("El ítem '{0}' tiene estado QC '{1}' pero no tiene causa especificada. "
                      "Debe indicar la razón del rechazo o cuarentena en el campo 'Causa de Rechazo/Cuarentena' "
                      "(custom_qc_rejection_reason) para poder guardar el documento. "
                      "Ejemplos de causas: 'Producto dañado', 'Embalaje defectuoso', 'Vencimiento corto', etc.").format(
                        frappe.bold(item.item_code),
                        frappe.bold(qc_status)
                    ),
                    title=_("Causa de Rechazo/Cuarentena Requerida - Documentación Obligatoria")
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
        Invariante DDD: Productos con vencimiento bajo umbral deben ir a Cuarentena automáticamente.
        
        FR17: Realizar control de calidad básico durante recepción
        
        Los productos con fecha de vencimiento muy cercana (bajo umbral configurable)
        representan un riesgo operativo y deben ser puestos en cuarentena automáticamente
        para revisión administrativa antes de estar disponibles para venta.
        
        El umbral se configura con prioridad:
        1. Purchase Receipt (custom_minimum_expiry_months) - si es diferente de 6
        2. Item Group (custom_minimum_expiry_months)
        3. Company (custom_minimum_expiry_months)
        4. Default: 6 meses
        
        Validación permisiva: ajusta automáticamente el estado QC a "Cuarentena" y
        establece la causa como "Vencimiento corto" si el producto está bajo el umbral.
        Solo ajusta si el estado actual es "Aceptado" (no sobrescribe decisiones manuales).
        
        Nota: Esta validación no lanza error, solo ajusta el estado automáticamente.
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
        Invariante DDD: Sobrantes no pueden estar disponibles para venta hasta decisión administrativa.
        
        FR17: Realizar control de calidad básico durante recepción
        
        Los sobrantes (productos recibidos en cantidad mayor a la ordenada) requieren
        revisión administrativa antes de estar disponibles para venta. Esta validación
        asegura que todos los sobrantes sean puestos automáticamente en Cuarentena
        hasta que se tome una decisión administrativa explícita.
        
        Validación permisiva: ajusta automáticamente el estado QC a "Cuarentena" y
        establece la causa como "Sobrante no autorizado" si el item está marcado como sobrante.
        Solo ajusta si el estado actual es "Aceptado" (no sobrescribe decisiones manuales).
        
        Nota: Esta validación no lanza error, solo ajusta el estado automáticamente.
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
                    # Establecer causa si no está establecida
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
            
            insert_and_submit_shelf_movement(movement)
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
