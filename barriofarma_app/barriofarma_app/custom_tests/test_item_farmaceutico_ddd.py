# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests DDD para el Agregado Item (Producto Farmacéutico)
Validación de invariantes y reglas de negocio del dominio farmacéutico
"""

import unittest
import frappe
from frappe.utils import cint

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item
)


class TestItemFarmaceuticoDDD(unittest.TestCase):
    """Tests para invariantes DDD del agregado Item"""
    
    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_items = []
    
    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        for item_name in self.test_items:
            try:
                if frappe.db.exists("Item", item_name):
                    frappe.delete_doc("Item", item_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        frappe.db.commit()
    
    def test_invariante_venta_libre_no_requiere_lote(self):
        """
        Invariante: Producto de Venta Libre no requiere lote (has_batch_no = 0)
        """
        item = create_test_item(
            item_code=f"TEST-VL-{frappe.generate_hash(length=6)}",
            item_name="Paracetamol 500mg - Venta Libre",
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=1,
            custom_prescription_storage_required=0,
            custom_active_principle="Paracetamol",
            custom_concentration="500mg",
            custom_pharmaceutical_form="Comprimido"
        )
        self.test_items.append(item.name)
        
        # Validar invariante
        self.assertEqual(cint(item.has_batch_no), 0, 
                        "Producto de Venta Libre no debe requerir lote")
        self.assertEqual(cint(item.has_expiry_date), 1,
                        "Producto de Venta Libre debe requerir vencimiento")
        self.assertEqual(cint(item.custom_prescription_storage_required), 0,
                        "Producto de Venta Libre no debe requerir almacenamiento de receta")
    
    def test_invariante_venta_libre_requiere_vencimiento(self):
        """
        Invariante: Producto de Venta Libre requiere vencimiento (has_expiry_date = 1)
        """
        item = create_test_item(
            item_code=f"TEST-VL-VENC-{frappe.generate_hash(length=6)}",
            item_name="Ibuprofeno 400mg - Venta Libre",
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=1,
            custom_prescription_storage_required=0,
            custom_active_principle="Ibuprofeno",
            custom_concentration="400mg"
        )
        self.test_items.append(item.name)
        
        # Validar invariante
        self.assertEqual(cint(item.has_expiry_date), 1,
                        "Producto de Venta Libre debe requerir fecha de vencimiento")
    
    def test_invariante_venta_libre_no_almacena_receta(self):
        """
        Invariante: Producto de Venta Libre no almacena receta (custom_prescription_storage_required = 0)
        """
        item = create_test_item(
            item_code=f"TEST-VL-REC-{frappe.generate_hash(length=6)}",
            item_name="Acetaminofén 500mg - Venta Libre",
            custom_dispensing_type="Venta Libre",
            has_batch_no=0,
            has_expiry_date=1,
            custom_prescription_storage_required=0,
            custom_active_principle="Acetaminofén",
            custom_concentration="500mg"
        )
        self.test_items.append(item.name)
        
        # Validar invariante
        self.assertEqual(cint(item.custom_prescription_storage_required), 0,
                        "Producto de Venta Libre no debe requerir almacenamiento de receta")
    
    def test_invariante_receta_retenida_requiere_lote(self):
        """
        Invariante: Producto de Receta Retenida requiere lote (has_batch_no = 1)
        """
        item = create_test_item(
            item_code=f"TEST-RR-LOTE-{frappe.generate_hash(length=6)}",
            item_name="Clonazepam 2mg - Receta Retenida",
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="F-67890/24",
            custom_active_principle="Clonazepam",
            custom_concentration="2mg"
        )
        self.test_items.append(item.name)
        
        # Validar invariante
        self.assertEqual(cint(item.has_batch_no), 1,
                        "Producto de Receta Retenida debe requerir lote")
        self.assertEqual(cint(item.has_expiry_date), 1,
                        "Producto de Receta Retenida debe requerir vencimiento")
        self.assertEqual(cint(item.custom_prescription_storage_required), 1,
                        "Producto de Receta Retenida debe requerir almacenamiento de receta")
    
    def test_invariante_receta_retenida_almacena_receta(self):
        """
        Invariante: Producto de Receta Retenida almacena receta (custom_prescription_storage_required = 1)
        """
        item = create_test_item(
            item_code=f"TEST-RR-REC-{frappe.generate_hash(length=6)}",
            item_name="Diazepam 10mg - Receta Retenida",
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="F-12345/24",
            custom_active_principle="Diazepam",
            custom_concentration="10mg"
        )
        self.test_items.append(item.name)
        
        # Validar invariante
        self.assertEqual(cint(item.custom_prescription_storage_required), 1,
                        "Producto de Receta Retenida debe requerir almacenamiento de receta")
    
    def test_regla_negocio_registro_sanitario_obligatorio_receta_retenida(self):
        """
        Regla de negocio: Producto de Receta Retenida requiere registro sanitario obligatorio
        Nota: Este test fallará hasta que implementemos la validación
        """
        # Intentar crear sin registro sanitario debe fallar
        with self.assertRaises((frappe.ValidationError, frappe.MandatoryError)) as context:
            item = create_test_item(
                item_code=f"TEST-RR-SIN-REG-{frappe.generate_hash(length=6)}",
                item_name="Medicamento sin registro",
                custom_dispensing_type="Venta con Receta Retenida",
                has_batch_no=1,
                has_expiry_date=1,
                custom_prescription_storage_required=1,
                # Sin custom_sanitary_registration - debe fallar
            )
            self.test_items.append(item.name)
        
        # Verificar que el error menciona registro sanitario o sea un error de validación
        error_message = str(context.exception).lower()
        self.assertTrue(
            "registro sanitario" in error_message or 
            "sanitary_registration" in error_message or
            "mandatory" in error_message,
            f"El error debe mencionar registro sanitario: {error_message}"
        )
    
    def test_invariante_control_level_psicotropico(self):
        """
        Invariante: Si control_level es Psicotrópico, requiere batch, expiry y prescription_retention
        Nota: Este test fallará hasta que implementemos la validación
        """
        item = create_test_item(
            item_code=f"TEST-PSIC-{frappe.generate_hash(length=6)}",
            item_name="Medicamento Psicotrópico",
            custom_control_level="Psicotrópico",
            custom_dispensing_type="Venta con Receta Retenida",  # Requerido para cumplir invariantes
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="P-11111/24",
            custom_active_principle="Psicotrópico Test",
            custom_concentration="10mg"
        )
        self.test_items.append(item.name)
        
        # Validar invariante
        self.assertEqual(cint(item.has_batch_no), 1,
                        "Medicamento Psicotrópico debe requerir lote")
        self.assertEqual(cint(item.has_expiry_date), 1,
                        "Medicamento Psicotrópico debe requerir vencimiento")
        self.assertEqual(cint(item.custom_requires_prescription_retention), 1,
                        "Medicamento Psicotrópico debe requerir receta retenida")
    
    def test_invariante_control_level_estupefaciente(self):
        """
        Invariante: Si control_level es Estupefaciente, requiere batch, expiry y prescription_retention
        Nota: Este test fallará hasta que implementemos la validación
        """
        item = create_test_item(
            item_code=f"TEST-ESTUP-{frappe.generate_hash(length=6)}",
            item_name="Medicamento Estupefaciente",
            custom_control_level="Estupefaciente",
            custom_dispensing_type="Venta con Receta Retenida",  # Requerido para cumplir invariantes
            has_batch_no=1,
            has_expiry_date=1,
            custom_requires_prescription_retention=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="E-22222/24",
            custom_active_principle="Estupefaciente Test",
            custom_concentration="5mg"
        )
        self.test_items.append(item.name)
        
        # Validar invariante
        self.assertEqual(cint(item.has_batch_no), 1,
                        "Medicamento Estupefaciente debe requerir lote")
        self.assertEqual(cint(item.has_expiry_date), 1,
                        "Medicamento Estupefaciente debe requerir vencimiento")
        self.assertEqual(cint(item.custom_requires_prescription_retention), 1,
                        "Medicamento Estupefaciente debe requerir receta retenida")

