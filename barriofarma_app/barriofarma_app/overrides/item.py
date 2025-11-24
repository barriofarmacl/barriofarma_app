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
        shelf_names = []
        
        for shelf_location in self.custom_shelf_locations:
            shelf_name = shelf_location.get("shelf")
            
            # Validar que el shelf existe
            if shelf_name and not frappe.db.exists("Shelf", shelf_name):
                frappe.throw(
                    _("El estante {0} no existe").format(frappe.bold(shelf_name)),
                    title=_("Estante Inválido")
                )
            
            # Contar ubicaciones preferidas
            if shelf_location.get("preferred_location"):
                preferred_count += 1
            
            # Validar compatibilidad tipo estante-producto
            if shelf_name:
                shelf_doc = frappe.get_doc("Shelf", shelf_name)
                shelf_type = shelf_doc.get("shelf_type")
                
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

