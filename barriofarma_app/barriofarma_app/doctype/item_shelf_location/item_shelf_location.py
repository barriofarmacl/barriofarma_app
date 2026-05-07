# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

import frappe
from frappe.model.document import Document


class ItemShelfLocation(Document):
	"""Child Table para relación Item-Shelf"""

	def validate(self):
		"""Validaciones de integridad para relación Item-Estante."""
		self.validate_quantity()

	def before_save(self):
		"""Actualizar last_updated antes de guardar."""
		from frappe.utils import now
		self.last_updated = now()

	def validate_quantity(self):
		"""La cantidad registrada en estante no puede ser negativa."""
		qty = float(self.quantity or 0)
		if qty < 0:
			frappe.throw("Cantidad en estante no puede ser negativa", frappe.ValidationError)

