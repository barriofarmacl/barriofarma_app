# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
DocType Shelf Movement - Registro de movimientos entre estantes
"""

import frappe
from frappe.model.document import Document
from frappe import _


class ShelfMovement(Document):
	"""
	Agregado Shelf Movement: Registra movimientos de productos entre estantes
	"""
	
	def validate(self):
		"""
		Validar invariantes del dominio antes de guardar
		"""
		self.validate_movement_type()
		self.validate_shelf()
		self.validate_item()
		self.validate_quantity()
		self.validate_transfer_destination()
	
	def validate_movement_type(self):
		"""
		Invariante: movement_type debe ser válido
		"""
		valid_types = ["Transferencia", "Recepción", "Venta", "Ajuste"]
		if self.movement_type not in valid_types:
			frappe.throw(
				_("Tipo de movimiento inválido: {0}. Debe ser uno de: {1}").format(
					self.movement_type, ", ".join(valid_types)
				),
				frappe.ValidationError
			)
	
	def validate_shelf(self):
		"""
		Invariante: Shelf debe existir y ser válido
		"""
		if not self.shelf:
			frappe.throw(_("Estante es obligatorio"), frappe.MandatoryError)
		
		if not frappe.db.exists("Shelf", self.shelf):
			frappe.throw(
				_("El estante {0} no existe").format(self.shelf),
				frappe.LinkValidationError
			)
		
		# Validar que el shelf no esté deshabilitado
		shelf_disabled = frappe.db.get_value("Shelf", self.shelf, "disabled")
		if shelf_disabled:
			frappe.throw(
				_("No se puede crear movimiento en estante deshabilitado: {0}").format(self.shelf),
				frappe.ValidationError
			)
	
	def validate_item(self):
		"""
		Invariante: Item debe existir
		"""
		if not self.item:
			frappe.throw(_("Producto es obligatorio"), frappe.MandatoryError)
		
		if not frappe.db.exists("Item", self.item):
			frappe.throw(
				_("El producto {0} no existe").format(self.item),
				frappe.LinkValidationError
			)
	
	def validate_quantity(self):
		"""
		Invariante: Cantidad debe ser positiva
		"""
		if not self.quantity:
			frappe.throw(_("Cantidad es obligatoria"), frappe.MandatoryError)
		
		if self.quantity <= 0:
			frappe.throw(
				_("La cantidad debe ser mayor que cero. Valor actual: {0}").format(self.quantity),
				frappe.ValidationError
			)
	
	def validate_transfer_destination(self):
		"""
		Invariante: Movimientos tipo Transferencia deben tener shelf destino
		"""
		if self.movement_type == "Transferencia":
			if not self.to_shelf:
				frappe.throw(
					_("Movimientos tipo Transferencia requieren un estante destino"),
					frappe.MandatoryError
				)
			
			if self.to_shelf == self.shelf:
				frappe.throw(
					_("El estante destino debe ser diferente al estante origen"),
					frappe.ValidationError
				)
			
			if not frappe.db.exists("Shelf", self.to_shelf):
				frappe.throw(
					_("El estante destino {0} no existe").format(self.to_shelf),
					frappe.LinkValidationError
				)
			
			# Validar que el shelf destino no esté deshabilitado
			to_shelf_disabled = frappe.db.get_value("Shelf", self.to_shelf, "disabled")
			if to_shelf_disabled:
				frappe.throw(
					_("No se puede transferir a estante deshabilitado: {0}").format(self.to_shelf),
					frappe.ValidationError
				)

