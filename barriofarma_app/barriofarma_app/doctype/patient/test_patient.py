# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para el DocType Patient
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


class TestPatient(FrappeTestCase):
	"""Tests para el DocType Patient"""

	def setUp(self):
		"""Preparar datos necesarios para cada test"""
		frappe.set_user("Administrator")
		self.test_patients = []
		self.test_customers = []

	def tearDown(self):
		"""Limpiar datos de prueba después de cada test"""
		frappe.set_user("Administrator")
		
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

	def test_create_patient_basic(self):
		"""Test: Crear paciente con datos básicos"""
		patient = frappe.get_doc({
			"doctype": "Patient",
			"patient_name": "Juan Pérez Test",
			"rut_dni": "12.345.678-9",
			"date_of_birth": "1980-01-15",
			"gender": "Masculino"
		})
		patient.insert(ignore_permissions=True)
		self.test_patients.append(patient.name)
		
		self.assertEqual(patient.patient_name, "Juan Pérez Test")
		self.assertEqual(patient.rut_dni, "12.345.678-9")
		self.assertIsNotNone(patient.customer, "Debe tener Customer asociado")

	def test_patient_creates_customer_automatically(self):
		"""Test: Verificar que se crea Customer automáticamente"""
		patient = frappe.get_doc({
			"doctype": "Patient",
			"patient_name": "María González Test",
			"rut_dni": "98.765.432-1"
		})
		patient.insert(ignore_permissions=True)
		self.test_patients.append(patient.name)
		
		# Verificar que Customer fue creado
		self.assertIsNotNone(patient.customer)
		self.assertTrue(frappe.db.exists("Customer", patient.customer))
		
		# Verificar que Customer tiene el mismo nombre
		customer = frappe.get_doc("Customer", patient.customer)
		self.assertEqual(customer.customer_name, patient.patient_name)

	def test_patient_rut_required(self):
		"""Test: Validar que el RUT es requerido"""
		with self.assertRaises(frappe.ValidationError) as cm:
			patient = frappe.get_doc({
				"doctype": "Patient",
				"patient_name": "Paciente Sin RUT",
				"rut_dni": ""  # RUT vacío
			})
			patient.insert(ignore_permissions=True)
		
		self.assertIn("rut", str(cm.exception).lower() or "dni" in str(cm.exception).lower())

	def test_patient_rut_unique(self):
		"""Test: Validar que el RUT debe ser único"""
		# Crear primer paciente
		patient1 = frappe.get_doc({
			"doctype": "Patient",
			"patient_name": "Paciente Uno",
			"rut_dni": "11.111.111-1"
		})
		patient1.insert(ignore_permissions=True)
		self.test_patients.append(patient1.name)
		
		# Intentar crear segundo paciente con mismo RUT
		with self.assertRaises(frappe.ValidationError) as cm:
			patient2 = frappe.get_doc({
				"doctype": "Patient",
				"patient_name": "Paciente Dos",
				"rut_dni": "11.111.111-1"  # Mismo RUT
			})
			patient2.insert(ignore_permissions=True)
		
		error_msg = str(cm.exception).lower()
		self.assertTrue(
			"duplicado" in error_msg or "ya existe" in error_msg,
			f"El error debe mencionar RUT duplicado: {error_msg}"
		)

	def test_patient_date_of_birth_validation(self):
		"""Test: Validar que la fecha de nacimiento no sea futura"""
		from frappe.utils import add_days, today
		future_date = add_days(today(), 365)
		
		with self.assertRaises(frappe.ValidationError) as cm:
			patient = frappe.get_doc({
				"doctype": "Patient",
				"patient_name": "Paciente Futuro",
				"rut_dni": "99.999.999-9",
				"date_of_birth": future_date
			})
			patient.insert(ignore_permissions=True)
		
		error_msg = str(cm.exception).lower()
		self.assertTrue(
			"futura" in error_msg or "fecha" in error_msg,
			f"El error debe mencionar fecha futura: {error_msg}"
		)

	def test_patient_syncs_with_customer(self):
		"""Test: Verificar sincronización con Customer"""
		patient = frappe.get_doc({
			"doctype": "Patient",
			"patient_name": "Carlos Rodríguez Test",
			"rut_dni": "77.777.777-7"
		})
		patient.insert(ignore_permissions=True)
		self.test_patients.append(patient.name)
		
		# Cambiar nombre del paciente
		patient.patient_name = "Carlos Rodríguez Actualizado"
		patient.save(ignore_permissions=True)
		
		# Verificar que Customer se actualizó
		customer = frappe.get_doc("Customer", patient.customer)
		self.assertEqual(customer.customer_name, "Carlos Rodríguez Actualizado")

	def test_patient_search_fields(self):
		"""Test: Validar que los campos de búsqueda funcionan"""
		patient = frappe.get_doc({
			"doctype": "Patient",
			"patient_name": "Búsqueda Test",
			"rut_dni": "TEST-RUT-001",
			"phone": "123456789",
			"email": "test@example.com"
		})
		patient.insert(ignore_permissions=True)
		self.test_patients.append(patient.name)
		
		# Buscar por nombre
		results = frappe.get_all("Patient", filters={"patient_name": ["like", "%Búsqueda%"]})
		self.assertGreater(len(results), 0)
		
		# Buscar por RUT
		results = frappe.get_all("Patient", filters={"rut_dni": "TEST-RUT-001"})
		self.assertEqual(len(results), 1)
		
		# Buscar por teléfono
		results = frappe.get_all("Patient", filters={"phone": "123456789"})
		self.assertGreater(len(results), 0)

