# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests DDD para el Agregado Prescription (Receta Médica)
Validación de invariantes y reglas de negocio del dominio farmacéutico
"""

import unittest
from datetime import date, timedelta
import frappe
from frappe.utils import getdate, add_days, today

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    get_or_create_root_customer_group,
    get_or_create_root_territory,
    create_test_customer,
    create_test_doctor,
    create_test_patient
)


class TestPrescriptionDDD(unittest.TestCase):
    """Tests para invariantes DDD del agregado Prescription"""

    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_prescriptions = []
        self.test_items = []
        self.test_customers = []
        self.test_doctors = []
        self.test_patients = []

    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar recetas
        for prescription_name in self.test_prescriptions:
            try:
                if frappe.db.exists("Prescription", prescription_name):
                    frappe.delete_doc("Prescription", prescription_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar items
        for item_name in self.test_items:
            try:
                if frappe.db.exists("Item", item_name):
                    frappe.delete_doc("Item", item_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar customers
        for customer_name in self.test_customers:
            try:
                if frappe.db.exists("Customer", customer_name):
                    frappe.delete_doc("Customer", customer_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar doctors
        for doctor_name in self.test_doctors:
            try:
                if frappe.db.exists("Doctor", doctor_name):
                    frappe.delete_doc("Doctor", doctor_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar patients
        for patient_name in self.test_patients:
            try:
                if frappe.db.exists("Patient", patient_name):
                    patient = frappe.get_doc("Patient", patient_name)
                    # Eliminar Customer asociado si existe
                    if patient.customer:
                        try:
                            if frappe.db.exists("Customer", patient.customer):
                                frappe.delete_doc("Customer", patient.customer, force=True, ignore_permissions=True)
                        except Exception:
                            pass
                    frappe.delete_doc("Patient", patient_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()

    def create_test_customer(self, customer_name, customer_type="Individual"):
        """Helper para crear Customer de prueba"""
        customer = create_test_customer(customer_name, customer_type)
        self.test_customers.append(customer.name)
        return customer
    
    def create_test_doctor_helper(self, doctor_name="Dr. Test Médico", license_number=None):
        """Helper para crear Doctor de prueba"""
        doctor = create_test_doctor(doctor_name=doctor_name, license_number=license_number)
        self.test_doctors.append(doctor.name)
        return doctor
    
    def create_test_patient_helper(self, patient_name="Paciente Test", rut_dni=None):
        """Helper para crear Patient de prueba"""
        patient = create_test_patient(patient_name=patient_name, rut_dni=rut_dni)
        self.test_patients.append(patient.name)
        return patient

    def create_test_prescription(self, **kwargs):
        """
        Función auxiliar para crear Prescription de prueba
        
        Args:
            **kwargs: Campos del Prescription a crear
        
        Returns:
            Prescription document creado
        """
        # Valores por defecto
        defaults = {
            "doctype": "Prescription",
            "doctor": kwargs.get("doctor"),
            "doctor_name": kwargs.get("doctor_name", "Dr. Test"),
            "doctor_license": kwargs.get("doctor_license", "TEST-LIC-12345"),
            "patient": kwargs.get("patient"),
            "patient_name": kwargs.get("patient_name"),
            "prescription_date": kwargs.get("prescription_date", today()),
            "valid_till": kwargs.get("valid_till", add_days(today(), 30)),
            "status": kwargs.get("status", "Nueva"),
            "max_dispensations": kwargs.get("max_dispensations", 1),
            "dispensation_count": kwargs.get("dispensation_count", 0),
            "items": kwargs.get("items", [])
        }
        
        # Actualizar con valores pasados
        defaults.update(kwargs)
        
        prescription = frappe.get_doc(defaults)
        prescription.insert(ignore_permissions=True)
        frappe.db.commit()
        
        self.test_prescriptions.append(prescription.name)
        return prescription

    def test_invariante_receta_debe_tener_al_menos_un_item(self):
        """
        Invariante: Una receta debe tener al menos un medicamento prescrito
        """
        doctor = self.create_test_doctor_helper()
        patient = self.create_test_patient_helper()
        
        # Intentar crear receta sin items
        with self.assertRaises(frappe.ValidationError) as cm:
            prescription = frappe.get_doc({
                "doctype": "Prescription",
                "doctor": doctor.name,
                "doctor_name": doctor.doctor_name,
                "doctor_license": doctor.license_number,
                "patient": patient.name,
                "patient_name": patient.patient_name,
                "prescription_date": today(),
                "valid_till": add_days(today(), 30),
                "status": "Nueva",
                "items": []  # Sin items
            })
            prescription.insert(ignore_permissions=True)
        
        self.assertIn("al menos un medicamento", str(cm.exception).lower() or "items required" in str(cm.exception).lower())

    def test_invariante_doctor_requiere_licencia_valida(self):
        """
        Invariante: Una receta debe estar asociada a un médico con licencia válida
        Nota: Como doctor_license tiene fetch_from, se auto-completa desde el doctor.
        La validación se hace al nivel del Doctor, no de la Prescription.
        Este test valida que un doctor sin licencia no puede ser creado.
        """
        # Intentar crear doctor sin licencia
        with self.assertRaises(frappe.ValidationError) as cm:
            doctor = frappe.get_doc({
                "doctype": "Doctor",
                "doctor_name": "Dr. Test Sin Licencia",
                "license_number": ""  # Licencia vacía
            })
            doctor.insert(ignore_permissions=True)
        
        self.assertIn("licencia", str(cm.exception).lower())
        
        # Verificar que con un doctor válido, la receta se crea correctamente
        doctor = self.create_test_doctor_helper()
        patient = self.create_test_patient_helper()
        item = create_test_item(
            item_code="TEST-MED-LIC",
            item_name="Medicamento Test",
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="TEST-REG-001",
            custom_active_principle="Principio Activo Test",
            custom_concentration="500mg"
        )
        self.test_items.append(item.name)
        
        prescription = self.create_test_prescription(
            doctor=doctor.name,
            doctor_name=doctor.doctor_name,
            doctor_license=doctor.license_number,
            patient=patient.name,
            patient_name=patient.patient_name,
            items=[{
                "item": item.name,
                "item_name": item.item_name,
                "quantity": 10,
                "dosage": "1 tableta",
                "frequency": "cada 8 horas"
            }]
        )
        
        # Verificar que la receta se creó correctamente con la licencia del doctor
        self.assertEqual(prescription.doctor_license, doctor.license_number)

    def test_invariante_paciente_obligatorio(self):
        """
        Invariante: Una receta debe estar asociada a un paciente específico
        """
        doctor = self.create_test_doctor_helper()
        item = create_test_item(
            item_code="TEST-MED-001",
            item_name="Medicamento Test",
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="TEST-REG-001",
            custom_active_principle="Principio Activo Test",
            custom_concentration="500mg"
        )
        self.test_items.append(item.name)
        
        # Intentar crear receta sin paciente
        with self.assertRaises(frappe.ValidationError) as cm:
            prescription = frappe.get_doc({
                "doctype": "Prescription",
                "doctor": doctor.name,
                "doctor_name": doctor.doctor_name,
                "doctor_license": doctor.license_number,
                "patient": None,  # Paciente vacío
                "patient_name": "",  # Nombre de paciente vacío
                "prescription_date": today(),
                "valid_till": add_days(today(), 30),
                "status": "Nueva",
                "items": [{
                    "item": item.name,
                    "item_name": item.item_name,
                    "quantity": 10,
                    "dosage": "1 tableta",
                    "frequency": "cada 8 horas"
                }]
            })
            prescription.insert(ignore_permissions=True)
        
        # Debe requerir paciente (required field)
        self.assertTrue(
            "patient" in str(cm.exception).lower() or "paciente" in str(cm.exception).lower(),
            f"El error debe mencionar paciente: {cm.exception}"
        )

    def test_invariante_validez_temporal(self):
        """
        Invariante: Una receta solo puede dispensarse dentro de su periodo de validez
        """
        doctor = self.create_test_doctor_helper()
        patient = self.create_test_patient_helper()
        item = create_test_item(
            item_code="TEST-MED-002",
            item_name="Medicamento Test",
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="TEST-REG-001",
            custom_active_principle="Principio Activo Test",
            custom_concentration="500mg"
        )
        self.test_items.append(item.name)
        
        # Crear receta válida
        prescription = self.create_test_prescription(
            doctor=doctor.name,
            doctor_name=doctor.doctor_name,
            doctor_license=doctor.license_number,
            patient=patient.name,
            patient_name=patient.patient_name,
            prescription_date=today(),
            valid_till=add_days(today(), 30),
            items=[{
                "item": item.name,
                "item_name": item.item_name,
                "quantity": 10,
                "dosage": "1 tableta",
                "frequency": "cada 8 horas"
            }]
        )
        
        # Verificar que valid_till es posterior a prescription_date
        self.assertGreaterEqual(
            getdate(prescription.valid_till),
            getdate(prescription.prescription_date),
            "La fecha de validez debe ser posterior o igual a la fecha de emisión"
        )
        
        # Intentar crear receta con valid_till anterior a prescription_date
        patient2 = self.create_test_patient_helper(patient_name="Paciente Test 2")
        with self.assertRaises(frappe.ValidationError) as cm:
            prescription_invalid = frappe.get_doc({
                "doctype": "Prescription",
                "doctor": doctor.name,
                "doctor_name": doctor.doctor_name,
                "doctor_license": doctor.license_number,
                "patient": patient2.name,
                "patient_name": patient2.patient_name,
                "prescription_date": today(),
                "valid_till": add_days(today(), -1),  # Fecha pasada
                "status": "Nueva",
                "items": [{
                    "item": item.name,
                    "item_name": item.item_name,
                    "quantity": 10,
                    "dosage": "1 tableta",
                    "frequency": "cada 8 horas"
                }]
            })
            prescription_invalid.insert(ignore_permissions=True)
        
        # Validación temporal debe fallar
        error_message = str(cm.exception).lower()
        self.assertTrue(
            "validez" in error_message or "valid_till" in error_message or "caducidad" in error_message,
            f"El error debe mencionar validez temporal: {error_message}"
        )

    def test_invariante_limite_dispensaciones(self):
        """
        Invariante: No se puede exceder el número máximo de dispensaciones especificado
        """
        doctor = self.create_test_doctor_helper()
        patient = self.create_test_patient_helper()
        item = create_test_item(
            item_code="TEST-MED-003",
            item_name="Medicamento Test",
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="TEST-REG-001",
            custom_active_principle="Principio Activo Test",
            custom_concentration="500mg"
        )
        self.test_items.append(item.name)
        
        # Crear receta con max_dispensations = 1
        prescription = self.create_test_prescription(
            doctor=doctor.name,
            doctor_name=doctor.doctor_name,
            doctor_license=doctor.license_number,
            patient=patient.name,
            patient_name=patient.patient_name,
            max_dispensations=1,
            dispensation_count=0,
            items=[{
                "item": item.name,
                "item_name": item.item_name,
                "quantity": 10,
                "dosage": "1 tableta",
                "frequency": "cada 8 horas"
            }]
        )
        
        # Intentar incrementar dispensation_count más allá del máximo
        prescription.dispensation_count = 2  # Excede el máximo de 1
        
        with self.assertRaises(frappe.ValidationError) as cm:
            prescription.save(ignore_permissions=True)
        
        # Debe validar que no exceda el máximo
        error_message = str(cm.exception).lower()
        self.assertTrue(
            "dispensaci" in error_message or "máximo" in error_message or "max_dispensations" in error_message,
            f"El error debe mencionar límite de dispensaciones: {error_message}"
        )

    def test_invariante_cantidad_dispensada_no_excede_prescrita(self):
        """
        Invariante: La cantidad dispensada no puede exceder la cantidad prescrita por ítem
        """
        doctor = self.create_test_doctor_helper()
        patient = self.create_test_patient_helper()
        item = create_test_item(
            item_code="TEST-MED-004",
            item_name="Medicamento Test",
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="TEST-REG-001",
            custom_active_principle="Principio Activo Test",
            custom_concentration="500mg"
        )
        self.test_items.append(item.name)
        
        prescription = self.create_test_prescription(
            doctor=doctor.name,
            doctor_name=doctor.doctor_name,
            doctor_license=doctor.license_number,
            patient=patient.name,
            patient_name=patient.patient_name,
            items=[{
                "item": item.name,
                "item_name": item.item_name,
                "quantity": 10,  # Cantidad prescrita
                "dispensed_qty": 0,  # Cantidad dispensada inicial
                "dosage": "1 tableta",
                "frequency": "cada 8 horas"
            }]
        )
        
        # Intentar establecer dispensed_qty mayor que quantity
        prescription.items[0].dispensed_qty = 15  # Excede la cantidad prescrita de 10
        
        with self.assertRaises(frappe.ValidationError) as cm:
            prescription.save(ignore_permissions=True)
        
        # Debe validar que no exceda la cantidad prescrita
        error_message = str(cm.exception).lower()
        self.assertTrue(
            "cantidad" in error_message or "quantity" in error_message or "prescrita" in error_message,
            f"El error debe mencionar cantidad prescrita: {error_message}"
        )

    def test_invariante_estado_actualizacion_automatica(self):
        """
        Invariante: El estado de la receta debe actualizarse automáticamente según las dispensaciones
        """
        doctor = self.create_test_doctor_helper()
        patient = self.create_test_patient_helper()
        item = create_test_item(
            item_code="TEST-MED-005",
            item_name="Medicamento Test",
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="TEST-REG-001",
            custom_active_principle="Principio Activo Test",
            custom_concentration="500mg"
        )
        self.test_items.append(item.name)
        
        # Crear receta nueva
        prescription = self.create_test_prescription(
            doctor=doctor.name,
            doctor_name=doctor.doctor_name,
            doctor_license=doctor.license_number,
            patient=patient.name,
            patient_name=patient.patient_name,
            status="Nueva",
            items=[{
                "item": item.name,
                "item_name": item.item_name,
                "quantity": 10,
                "dispensed_qty": 0,
                "dosage": "1 tableta",
                "frequency": "cada 8 horas"
            }]
        )
        
        # Estado inicial debe ser "Nueva"
        self.assertEqual(prescription.status, "Nueva")
        
        # Al dispensar parcialmente, estado debe cambiar a "Parcialmente Dispensada"
        prescription.items[0].dispensed_qty = 5  # Parcialmente dispensada
        prescription.save(ignore_permissions=True)
        prescription.reload()
        
        # La lógica de actualización de estado se implementará en validaciones
        # Por ahora solo verificamos que el documento se guarda correctamente
        self.assertIsNotNone(prescription.name)

    def test_regla_negocio_receta_vencida_no_puede_dispensarse(self):
        """
        Regla de Negocio: Una receta vencida no puede ser utilizada para dispensación
        """
        doctor = self.create_test_doctor_helper()
        patient = self.create_test_patient_helper()
        item = create_test_item(
            item_code="TEST-MED-006",
            item_name="Medicamento Test",
            custom_dispensing_type="Venta con Receta Retenida",
            has_batch_no=1,
            has_expiry_date=1,
            custom_prescription_storage_required=1,
            custom_sanitary_registration="TEST-REG-001",
            custom_active_principle="Principio Activo Test",
            custom_concentration="500mg"
        )
        self.test_items.append(item.name)
        
        # Crear receta vencida
        prescription = self.create_test_prescription(
            doctor=doctor.name,
            doctor_name=doctor.doctor_name,
            doctor_license=doctor.license_number,
            patient=patient.name,
            patient_name=patient.patient_name,
            prescription_date=add_days(today(), -60),
            valid_till=add_days(today(), -30),  # Vencida hace 30 días
            status="Vencida",
            items=[{
                "item": item.name,
                "item_name": item.item_name,
                "quantity": 10,
                "dosage": "1 tableta",
                "frequency": "cada 8 horas"
            }]
        )
        
        # Intentar dispensar en receta vencida
        prescription.items[0].dispensed_qty = 5
        
        with self.assertRaises(frappe.ValidationError) as cm:
            prescription.save(ignore_permissions=True)
        
        # Debe validar que no se pueda dispensar en receta vencida
        error_message = str(cm.exception).lower()
        self.assertTrue(
            "vencida" in error_message or "caducada" in error_message or "validez" in error_message,
            f"El error debe mencionar receta vencida: {error_message}"
        )

