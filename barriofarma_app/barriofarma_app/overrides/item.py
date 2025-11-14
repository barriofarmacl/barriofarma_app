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
    """
    Extensión de la clase Item de ERPNext para agregar validaciones
    específicas del dominio farmacéutico según el modelo DDD
    """
    
    def validate(self):
        """
        Valida las invariantes del agregado Item según el modelo DDD
        """
        # Llamar al método validate de la clase padre primero
        super().validate()
        
        # Validar invariantes del dominio farmacéutico
        self.validate_control_level_invariants()
        self.validate_dispensing_type_invariants()
        self.validate_sanitary_registration_required()
    
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
        - Venta Libre: has_batch_no = 0, custom_prescription_storage_required = 0
        - Venta con Receta Retenida: has_batch_no = 1, custom_prescription_storage_required = 1
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
                # No lanzamos error, solo ajustamos automáticamente para cumplir invariante
                self.set("custom_prescription_storage_required", 1)
    
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

