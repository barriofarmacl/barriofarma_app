# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
DocType Patient para gestionar información de pacientes
Integrado con Customer para compatibilidad con ERPNext
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class Patient(Document):
	"""
	Extensión de la clase Patient para implementar validaciones
	y creación automática de Customer
	"""

	def validate(self):
		"""
		Valida las invariantes del agregado Patient según el modelo DDD
		"""
		self.validate_rut_dni_required()
		self.validate_rut_dni_unique()
		self.validate_date_of_birth()
		
		# Crear o actualizar Customer asociado
		if not self.is_new():
			self.sync_with_customer()

	def before_insert(self):
		"""
		Antes de insertar, crear Customer asociado
		"""
		self.create_customer()

	def validate_rut_dni_required(self):
		"""
		Invariante: Un paciente debe tener RUT/DNI válido
		"""
		if not self.get("rut_dni") or not self.get("rut_dni").strip():
			frappe.throw(
				_("El RUT/DNI (rut_dni) es obligatorio"),
				title=_("RUT/DNI Requerido")
			)

	def validate_rut_dni_unique(self):
		"""
		Invariante: El RUT/DNI debe ser único
		"""
		if self.get("rut_dni"):
			existing_patient = frappe.db.get_value(
				"Patient",
				{"rut_dni": self.rut_dni},
				"name"
			)
			if existing_patient and existing_patient != self.name:
				frappe.throw(
					_("Ya existe un paciente con el RUT/DNI '{0}'").format(
						self.rut_dni
					),
					title=_("RUT/DNI Duplicado")
				)

	def validate_date_of_birth(self):
		"""
		Validar que la fecha de nacimiento no sea futura
		"""
		if self.get("date_of_birth"):
			birth_date = getdate(self.date_of_birth)
			today = getdate()
			if birth_date > today:
				frappe.throw(
					_("La fecha de nacimiento no puede ser futura"),
					title=_("Fecha Inválida")
				)

	def create_customer(self):
		"""
		Crear Customer automáticamente al crear Patient
		"""
		if self.get("customer"):
			# Ya tiene Customer asociado, no crear otro
			return
		
		# Verificar si ya existe un Customer con el mismo nombre
		existing_customer = frappe.db.get_value(
			"Customer",
			{"customer_name": self.patient_name},
			"name"
		)
		
		if existing_customer:
			# Usar Customer existente
			self.customer = existing_customer
		else:
			# Crear nuevo Customer
			from barriofarma_app.barriofarma_app.test_setup import (
				get_or_create_root_customer_group,
				get_or_create_root_territory
			)
			
			customer_group = get_or_create_root_customer_group()
			territory = get_or_create_root_territory()
			
			customer = frappe.get_doc({
				"doctype": "Customer",
				"customer_name": self.patient_name,
				"customer_type": "Individual",
				"customer_group": customer_group,
				"territory": territory,
			})
			customer.insert(ignore_permissions=True)
			frappe.db.commit()
			
			self.customer = customer.name

	def sync_with_customer(self):
		"""
		Sincronizar datos con Customer asociado
		"""
		if not self.get("customer"):
			return
		
		try:
			customer = frappe.get_doc("Customer", self.customer)
			
			# Sincronizar nombre si cambió
			if customer.customer_name != self.patient_name:
				customer.customer_name = self.patient_name
				customer.save(ignore_permissions=True)
				frappe.db.commit()
		except frappe.DoesNotExistError:
			# Customer no existe, crear uno nuevo
			self.create_customer()

