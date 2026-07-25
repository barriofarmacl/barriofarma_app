# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Override del DocType Item para implementar validaciones DDD del dominio farmacéutico
"""

import frappe
from frappe import _
from erpnext.stock.doctype.item.item import Item as ERPNextItem


class Item(ERPNextItem):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from erpnext.stock.doctype.item_barcode.item_barcode import ItemBarcode
        from erpnext.stock.doctype.item_customer_detail.item_customer_detail import ItemCustomerDetail
        from erpnext.stock.doctype.item_default.item_default import ItemDefault
        from erpnext.stock.doctype.item_reorder.item_reorder import ItemReorder
        from erpnext.stock.doctype.item_supplier.item_supplier import ItemSupplier
        from erpnext.stock.doctype.item_tax.item_tax import ItemTax
        from erpnext.stock.doctype.item_variant_attribute.item_variant_attribute import ItemVariantAttribute
        from erpnext.stock.doctype.uom_conversion_detail.uom_conversion_detail import UOMConversionDetail
        from frappe.types import DF

        allow_alternative_item: DF.Check
        allow_negative_stock: DF.Check
        asset_category: DF.Link | None
        asset_naming_series: DF.Literal[None]
        attributes: DF.Table[ItemVariantAttribute]
        auto_create_assets: DF.Check
        barcodes: DF.Table[ItemBarcode]
        batch_number_series: DF.Data | None
        brand: DF.Link | None
        country_of_origin: DF.Link | None
        create_new_batch: DF.Check
        customer: DF.Link | None
        customer_code: DF.SmallText | None
        customer_items: DF.Table[ItemCustomerDetail]
        customs_tariff_number: DF.Link | None
        default_bom: DF.Link | None
        default_item_manufacturer: DF.Link | None
        default_manufacturer_part_no: DF.Data | None
        default_material_request_type: DF.Literal["Purchase", "Material Transfer", "Material Issue", "Manufacture", "Customer Provided"]
        delivered_by_supplier: DF.Check
        description: DF.TextEditor | None
        disabled: DF.Check
        enable_deferred_expense: DF.Check
        enable_deferred_revenue: DF.Check
        end_of_life: DF.Date | None
        grant_commission: DF.Check
        has_batch_no: DF.Check
        has_expiry_date: DF.Check
        has_serial_no: DF.Check
        has_variants: DF.Check
        image: DF.AttachImage | None
        include_item_in_manufacturing: DF.Check
        inspection_required_before_delivery: DF.Check
        inspection_required_before_purchase: DF.Check
        is_customer_provided_item: DF.Check
        is_fixed_asset: DF.Check
        is_grouped_asset: DF.Check
        is_purchase_item: DF.Check
        is_sales_item: DF.Check
        is_stock_item: DF.Check
        is_sub_contracted_item: DF.Check
        item_code: DF.Data
        item_defaults: DF.Table[ItemDefault]
        item_group: DF.Link
        item_name: DF.Data | None
        last_purchase_rate: DF.Float
        lead_time_days: DF.Int
        max_discount: DF.Float
        min_order_qty: DF.Float
        naming_series: DF.Literal["STO-ITEM-.YYYY.-"]
        no_of_months: DF.Int
        no_of_months_exp: DF.Int
        opening_stock: DF.Float
        over_billing_allowance: DF.Float
        over_delivery_receipt_allowance: DF.Float
        purchase_uom: DF.Link | None
        quality_inspection_template: DF.Link | None
        reorder_levels: DF.Table[ItemReorder]
        retain_sample: DF.Check
        safety_stock: DF.Float
        sales_uom: DF.Link | None
        sample_quantity: DF.Int
        serial_no_series: DF.Data | None
        shelf_life_in_days: DF.Int
        standard_rate: DF.Currency
        stock_uom: DF.Link
        supplier_items: DF.Table[ItemSupplier]
        taxes: DF.Table[ItemTax]
        total_projected_qty: DF.Float
        uoms: DF.Table[UOMConversionDetail]
        valuation_method: DF.Literal["", "FIFO", "Moving Average", "LIFO"]
        valuation_rate: DF.Currency
        variant_based_on: DF.Literal["Item Attribute", "Manufacturer"]
        variant_of: DF.Link | None
        warranty_period: DF.Data | None
        weight_per_unit: DF.Float
        weight_uom: DF.Link | None
    # end: auto-generated types
    """
    Extensión de la clase Item de ERPNext para agregar validaciones
    específicas del dominio farmacéutico según el modelo DDD
    """
    
    def before_insert(self):
        """Default farmacéutico para inserts sin tipo (p. ej. _Test Item de ERPNext)."""
        if not self.get("custom_dispensing_type"):
            self.custom_dispensing_type = "Venta Libre"

    def validate(self):
        """
        Valida las invariantes del agregado Item según el modelo DDD
        """
        # Llamar al método validate de la clase padre primero
        super().validate()
        
        # Validar invariantes del dominio farmacéutico
        # Dispensing primero: proyecta retention/storage antes de control_level
        self.validate_dispensing_type_invariants()
        self.validate_control_level_invariants()
        self.validate_sanitary_registration_required()
        self.validate_shelf_locations_invariants()
    
    def validate_control_level_invariants(self):
        """
        Invariante: Si custom_control_level es Psicotrópico o Estupefaciente,
        entonces has_batch_no, has_expiry_date y custom_requires_prescription_retention
        deben ser verdaderos (Check = 1)
        """
        control_level = self.get("custom_control_level")
        
        if control_level in ("Psicotrópico", "Estupefaciente"):
            if not self.get("has_batch_no"):
                frappe.throw(
                    _("Los medicamentos {0} deben requerir gestión por lote (has_batch_no debe estar marcado)").format(
                        frappe.bold(control_level)
                    ),
                    title=_("Invariante de Control No Cumplida")
                )
            
            if not self.get("has_expiry_date"):
                frappe.throw(
                    _("Los medicamentos {0} deben requerir gestión por fecha de vencimiento (has_expiry_date debe estar marcado)").format(
                        frappe.bold(control_level)
                    ),
                    title=_("Invariante de Control No Cumplida")
                )
            
            if not self.get("custom_requires_prescription_retention"):
                frappe.throw(
                    _("Los medicamentos {0} deben requerir receta retenida (custom_requires_prescription_retention debe estar marcado)").format(
                        frappe.bold(control_level)
                    ),
                    title=_("Invariante de Control No Cumplida")
                )
    
    def validate_dispensing_type_invariants(self):
        """
        Valida las invariantes según el tipo de dispensación:
        - Venta Libre: has_batch_no = 0, storage = 0, retention = 0
        - Venta con Receta Retenida: has_batch_no = 1, storage = 1, retention = 1

        custom_dispensing_type es la fuente de verdad; storage/retention se proyectan
        en validate (whiteboard #78 PR5).
        """
        dispensing_type = self.get("custom_dispensing_type")
        
        if not dispensing_type:
            # Si no hay tipo de dispensación definido, no validamos estas invariantes
            return
        
        if dispensing_type == "Venta Libre":
            # Venta Libre: no requiere lote ni almacenamiento de receta
            if self.get("has_batch_no"):
                # No lanzamos error, solo ajustamos automáticamente para cumplir invariante
                self.set("has_batch_no", 0)
            
            if self.get("custom_prescription_storage_required"):
                self.set("custom_prescription_storage_required", 0)

            if self.get("custom_requires_prescription_retention"):
                self.set("custom_requires_prescription_retention", 0)
            
            # Venta Libre siempre requiere vencimiento
            if not self.get("has_expiry_date"):
                self.set("has_expiry_date", 1)
        
        elif dispensing_type == "Venta con Receta Retenida":
            # Receta Retenida: requiere lote y almacenamiento de receta
            if not self.get("has_batch_no"):
                frappe.throw(
                    _("Los productos de 'Venta con Receta Retenida' deben requerir gestión por lote (has_batch_no debe estar marcado)"),
                    title=_("Invariante de Dispensación No Cumplida")
                )
            
            if not self.get("has_expiry_date"):
                frappe.throw(
                    _("Los productos de 'Venta con Receta Retenida' deben requerir gestión por fecha de vencimiento (has_expiry_date debe estar marcado)"),
                    title=_("Invariante de Dispensación No Cumplida")
                )
            
            if not self.get("custom_prescription_storage_required"):
                self.set("custom_prescription_storage_required", 1)

            if not self.get("custom_requires_prescription_retention"):
                self.set("custom_requires_prescription_retention", 1)
    
    def validate_sanitary_registration_required(self):
        """
        Regla de Negocio: Si custom_dispensing_type = "Venta con Receta Retenida",
        entonces custom_sanitary_registration es obligatorio
        """
        dispensing_type = self.get("custom_dispensing_type")
        
        if dispensing_type == "Venta con Receta Retenida":
            sanitary_registration = self.get("custom_sanitary_registration")
            
            if not sanitary_registration or not sanitary_registration.strip():
                frappe.throw(
                    _("El registro sanitario (custom_sanitary_registration) es obligatorio para productos de 'Venta con Receta Retenida'"),
                    title=_("Campo Obligatorio")
                )
    
    def validate_shelf_locations_invariants(self):
        """
        Valida las invariantes de la relación Item-Shelf:
        1. Shelf debe existir
        2. Solo puede haber una ubicación preferida por Item
        3. Tipo de estante compatible con tipo de producto:
           - Estantes Controlados solo productos con custom_control_level
           - Estantes Refrigerados solo productos que requieren refrigeración
        """
        if not hasattr(self, "custom_shelf_locations") or not self.custom_shelf_locations:
            return
        
        preferred_count = 0
        shelf_names = set()
        
        for shelf_location in self.custom_shelf_locations:
            shelf_name = shelf_location.get("shelf")
            qty = float(shelf_location.get("quantity") or 0)
            
            # Validar que el shelf existe
            if shelf_name and not frappe.db.exists("Shelf", shelf_name):
                frappe.throw(
                    _("El estante {0} no existe").format(frappe.bold(shelf_name)),
                    title=_("Estante Inválido")
                )

            # Evitar duplicar el mismo shelf para un item
            if shelf_name in shelf_names:
                frappe.throw(
                    _("El estante {0} está repetido en las ubicaciones del producto").format(
                        frappe.bold(shelf_name)
                    ),
                    title=_("Ubicación de Estante Duplicada")
                )
            if shelf_name:
                shelf_names.add(shelf_name)

            # Validar cantidad no negativa
            if qty < 0:
                frappe.throw(
                    _("La cantidad en estante no puede ser negativa para {0}").format(
                        frappe.bold(shelf_name or _("(sin estante)"))
                    ),
                    title=_("Cantidad Inválida en Estante")
                )
            
            # Contar ubicaciones preferidas
            if shelf_location.get("preferred_location"):
                preferred_count += 1
            
            # Validar compatibilidad tipo estante-producto
            if shelf_name:
                shelf_doc = frappe.get_doc("Shelf", shelf_name)
                shelf_type = shelf_doc.get("shelf_type")

                if shelf_doc.get("disabled"):
                    frappe.throw(
                        _("No se puede asignar producto al estante deshabilitado {0}").format(
                            frappe.bold(shelf_doc.shelf_name)
                        ),
                        title=_("Estante Deshabilitado")
                    )
                
                # Validar estante Controlado
                if shelf_type == "Controlado":
                    control_level = self.get("custom_control_level")
                    if not control_level or control_level == "None":
                        frappe.throw(
                            _("El estante {0} es de tipo Controlado y solo puede contener productos con nivel de control (Psicotrópico o Estupefaciente)").format(
                                frappe.bold(shelf_doc.shelf_name)
                            ),
                            title=_("Incompatibilidad Tipo Estante-Producto")
                        )
                
                # Validar estante Refrigerado
                if shelf_type == "Refrigerado":
                    requires_refrigeration = self.get("custom_requires_refrigeration")
                    if not requires_refrigeration:
                        frappe.throw(
                            _("El estante {0} es de tipo Refrigerado y solo puede contener productos que requieren refrigeración (custom_requires_refrigeration debe estar marcado)").format(
                                frappe.bold(shelf_doc.shelf_name)
                            ),
                            title=_("Incompatibilidad Tipo Estante-Producto")
                        )
                
                # Validar capacidad del shelf antes de agregar producto
                if shelf_doc.max_capacity:
                    # Calcular capacidad disponible
                    current_occupancy = shelf_doc.calculate_current_occupancy()
                    available_capacity = shelf_doc.max_capacity - current_occupancy
                    
                    # Obtener stock actual del item en el warehouse del shelf
                    from erpnext.stock.utils import get_or_make_bin
                    bin_name = get_or_make_bin(self.name, shelf_doc.warehouse)
                    bin_doc = frappe.get_doc("Bin", bin_name)
                    item_stock = bin_doc.actual_qty or 0.0
                    
                    # Si el stock del item excede la capacidad disponible, fallar
                    if item_stock > available_capacity:
                        frappe.throw(
                            _("No se puede agregar el producto al estante {0}: el stock del producto ({1}) excede la capacidad disponible ({2}) del estante (capacidad máxima: {3}, ocupación actual: {4})").format(
                                frappe.bold(shelf_doc.shelf_name),
                                item_stock,
                                available_capacity,
                                shelf_doc.max_capacity,
                                current_occupancy
                            ),
                            title=_("Capacidad del Estante Excedida")
                        )
        
        # Validar que solo hay una ubicación preferida
        if preferred_count > 1:
            frappe.throw(
                _("Solo puede haber una ubicación preferida por producto. Actualmente hay {0} marcadas como preferidas").format(
                    preferred_count
                ),
                title=_("Múltiples Ubicaciones Preferidas")
            )

        # Autocompletar cantidad por estante cuando sea inferible
        self._auto_fill_single_shelf_quantity()
        self._auto_fill_shelf_quantities_from_movements()

    def _auto_fill_single_shelf_quantity(self):
        """
        Si en un warehouse el item tiene exactamente un shelf y la cantidad está en 0,
        autocompletar con el stock real de Bin para ese warehouse.

        Regla conservadora: con múltiples estantes por warehouse no se distribuye
        automáticamente para evitar asignaciones incorrectas.
        """
        if not hasattr(self, "custom_shelf_locations") or not self.custom_shelf_locations:
            return

        shelves_by_warehouse = {}
        for row in self.custom_shelf_locations:
            shelf_name = row.get("shelf")
            if not shelf_name or not frappe.db.exists("Shelf", shelf_name):
                continue
            shelf_wh = frappe.db.get_value("Shelf", shelf_name, "warehouse")
            if not shelf_wh:
                continue
            shelves_by_warehouse.setdefault(shelf_wh, []).append(row)

        for warehouse, rows in shelves_by_warehouse.items():
            if len(rows) != 1:
                continue
            row = rows[0]

            bin_qty = (
                frappe.db.get_value(
                    "Bin",
                    {"item_code": self.name, "warehouse": warehouse},
                    "actual_qty",
                )
                or 0
            )
            # Un solo estante en warehouse => Bin es fuente de verdad operativa.
            row.quantity = float(bin_qty or 0)

    def _auto_fill_shelf_quantities_from_movements(self):
        """
        Sincronizar cantidad por estante desde Shelf Movement para filas con quantity=0.

        Política de seguridad:
        - Solo actualiza filas con quantity <= 0 (no sobreescribe ajustes manuales > 0).
        - Usa solo movimientos submitidos (docstatus=1).
        """
        if not hasattr(self, "custom_shelf_locations") or not self.custom_shelf_locations:
            return

        shelf_rows = [r for r in self.custom_shelf_locations if r.get("shelf")]
        if not shelf_rows:
            return

        movement_rows = frappe.db.sql(
            """
            SELECT t.shelf, SUM(t.delta_qty) AS qty
            FROM (
                SELECT
                    sm.shelf AS shelf,
                    CASE
                        WHEN sm.movement_type = 'Recepción' THEN sm.quantity
                        WHEN sm.movement_type = 'Transferencia' THEN -sm.quantity
                        WHEN sm.movement_type IN ('Venta', 'Ajuste') THEN -sm.quantity
                        ELSE 0
                    END AS delta_qty
                FROM `tabShelf Movement` sm
                WHERE sm.item = %(item_code)s
                    AND sm.docstatus = 1

                UNION ALL

                SELECT
                    sm.to_shelf AS shelf,
                    sm.quantity AS delta_qty
                FROM `tabShelf Movement` sm
                WHERE sm.item = %(item_code)s
                    AND sm.movement_type = 'Transferencia'
                    AND sm.to_shelf IS NOT NULL
                    AND sm.docstatus = 1
            ) t
            WHERE t.shelf IS NOT NULL
            GROUP BY t.shelf
            """,
            {"item_code": self.name},
            as_dict=True,
        )
        if not movement_rows:
            return

        qty_by_shelf = {r.get("shelf"): float(r.get("qty") or 0) for r in movement_rows}
        for row in shelf_rows:
            shelf = row.get("shelf")
            if not shelf:
                continue
            current_qty = float(row.get("quantity") or 0)
            if current_qty > 0:
                continue
            movement_qty = qty_by_shelf.get(shelf)
            if movement_qty is None:
                continue
            if movement_qty >= 0:
                row.quantity = movement_qty

