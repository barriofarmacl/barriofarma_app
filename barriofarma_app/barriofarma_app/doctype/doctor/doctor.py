# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
DocType Doctor para gestionar información de médicos prescriptores
Solo informativo, no vinculado a Customer
"""

import frappe
from frappe import _
from frappe.model.document import Document


class Doctor(Document):
	"""
	Extensión de la clase Doctor para implementar validaciones
	específicas del dominio farmacéutico
	"""

	def validate(self):
		"""
		Valida las invariantes del agregado Doctor según el modelo DDD
		"""
		self.validate_license_number_required()
		self.validate_license_number_unique()

	def validate_license_number_required(self):
		"""
		Invariante: Un médico debe tener un número de licencia válido
		"""
		if not self.get("license_number") or not self.get("license_number").strip():
			frappe.throw(
				_("El número de licencia médica (license_number) es obligatorio"),
				title=_("Licencia Médica Requerida")
			)

	def validate_license_number_unique(self):
		"""
		Invariante: El número de licencia debe ser único
		"""
		if self.get("license_number"):
			existing_doctor = frappe.db.get_value(
				"Doctor",
				{"license_number": self.license_number},
				"name"
			)
			if existing_doctor and existing_doctor != self.name:
				frappe.throw(
					_("Ya existe un médico con el número de licencia '{0}'").format(
						self.license_number
					),
					title=_("Licencia Duplicada")
				)

