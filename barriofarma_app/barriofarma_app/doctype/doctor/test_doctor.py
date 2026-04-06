# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para el DocType Doctor
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestDoctor(FrappeTestCase):
	"""Tests para el DocType Doctor"""

	def setUp(self):
		"""Preparar datos necesarios para cada test"""
		frappe.set_user("Administrator")
		self.test_doctors = []

	def tearDown(self):
		"""Limpiar datos de prueba después de cada test"""
		frappe.set_user("Administrator")
		
		for doctor_name in self.test_doctors:
			try:
				if frappe.db.exists("Doctor", doctor_name):
					frappe.delete_doc("Doctor", doctor_name, force=True, ignore_permissions=True)
			except Exception:
				pass
		
		frappe.db.commit()

	def test_create_doctor_basic(self):
		"""Test: Crear doctor con datos básicos"""
		doctor = frappe.get_doc({
			"doctype": "Doctor",
			"doctor_name": "Dr. Test Médico",
			"license_number": "TEST-LIC-001",
			"specialty": "Medicina General"
		})
		doctor.insert(ignore_permissions=True)
		self.test_doctors.append(doctor.name)
		
		self.assertEqual(doctor.doctor_name, "Dr. Test Médico")
		self.assertEqual(doctor.license_number, "TEST-LIC-001")
		self.assertEqual(doctor.specialty, "Medicina General")

	def test_doctor_license_required(self):
		"""Test: Validar que la licencia es requerida"""
		with self.assertRaises(frappe.ValidationError) as cm:
			doctor = frappe.get_doc({
				"doctype": "Doctor",
				"doctor_name": "Dr. Test Sin Licencia",
				"license_number": ""  # Licencia vacía
			})
			doctor.insert(ignore_permissions=True)
		
		self.assertIn("licencia", str(cm.exception).lower())

	def test_doctor_license_unique(self):
		"""Test: Validar que la licencia debe ser única"""
		# Crear primer doctor
		doctor1 = frappe.get_doc({
			"doctype": "Doctor",
			"doctor_name": "Dr. Test Uno",
			"license_number": "TEST-LIC-UNIQUE"
		})
		doctor1.insert(ignore_permissions=True)
		self.test_doctors.append(doctor1.name)
		
		# Intentar crear segundo doctor con misma licencia
		with self.assertRaises(frappe.ValidationError) as cm:
			doctor2 = frappe.get_doc({
				"doctype": "Doctor",
				"doctor_name": "Dr. Test Dos",
				"license_number": "TEST-LIC-UNIQUE"  # Misma licencia
			})
			doctor2.insert(ignore_permissions=True)
		
		error_msg = str(cm.exception).lower()
		self.assertTrue(
			"duplicada" in error_msg or "ya existe" in error_msg,
			f"El error debe mencionar licencia duplicada: {error_msg}"
		)

	def test_doctor_search_fields(self):
		"""Test: Validar que los campos de búsqueda funcionan"""
		doctor = frappe.get_doc({
			"doctype": "Doctor",
			"doctor_name": "Dr. Búsqueda Test",
			"license_number": "TEST-LIC-SEARCH",
			"specialty": "Cardiología"
		})
		doctor.insert(ignore_permissions=True)
		self.test_doctors.append(doctor.name)
		
		# Buscar por nombre
		results = frappe.get_all("Doctor", filters={"doctor_name": ["like", "%Búsqueda%"]})
		self.assertGreater(len(results), 0)
		
		# Buscar por licencia
		results = frappe.get_all("Doctor", filters={"license_number": "TEST-LIC-SEARCH"})
		self.assertEqual(len(results), 1)
		
		# Buscar por especialidad
		results = frappe.get_all("Doctor", filters={"specialty": ["like", "%Cardiología%"]})
		self.assertGreater(len(results), 0)

