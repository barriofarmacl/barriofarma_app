# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

import frappe
from frappe.model.document import Document


class ItemShelfLocation(Document):
	"""Child Table para relación Item-Shelf"""
	
	def before_save(self):
		"""Actualizar last_updated antes de guardar"""
		from frappe.utils import now
		self.last_updated = now()

