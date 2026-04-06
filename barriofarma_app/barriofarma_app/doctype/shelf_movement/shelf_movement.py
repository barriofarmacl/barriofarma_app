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
	
	def on_submit(self):
		"""
		Actualizar current_occupancy del Shelf después de submitir el movimiento
		Esto asegura que cuando se vende un producto, el shelf muestre el valor descontado
		"""
		self._update_shelf_occupancy()
	
	def on_cancel(self):
		"""
		Actualizar current_occupancy del Shelf después de cancelar el movimiento
		"""
		self._update_shelf_occupancy()
	
	def _update_shelf_occupancy(self):
		"""
		Actualizar current_occupancy de los shelves afectados por este movimiento
		Esto asegura que el shelf refleje el stock real después de ventas, transferencias, etc.
		
		Nota: La actualización del Bin en ERPNext es SÍNCRONA (no hay procesos asíncronos de Redis).
		Sin embargo, debemos asegurar que:
		1. El commit de la transacción actual esté completo
		2. Los datos del Bin estén frescos (sin caché)
		3. El cálculo se haga con los datos más recientes
		"""
		# Actualizar shelf origen (siempre existe)
		if self.shelf and frappe.db.exists("Shelf", self.shelf):
			try:
				# Forzar commit para asegurar que todos los cambios de stock (SLE, Bin) estén persistidos
				# Esto es importante porque el Stock Ledger Entry se crea en la misma transacción
				# pero el commit puede no estar completo cuando se ejecuta este hook
				frappe.db.commit()
				
				# Invalidar caché del Bin para asegurar que leemos datos frescos
				# Esto es necesario porque Frappe puede cachear consultas SQL
				frappe.clear_cache(doctype="Bin")
				
				# Recargar el shelf para obtener datos actualizados
				shelf_doc = frappe.get_doc("Shelf", self.shelf)
				shelf_doc.reload()
				
				if hasattr(shelf_doc, "calculate_current_occupancy"):
					# Calcular occupancy con datos frescos del Bin
					new_occupancy = shelf_doc.calculate_current_occupancy()
					shelf_doc.current_occupancy = new_occupancy
					shelf_doc.save(ignore_permissions=True)
					frappe.db.commit()
			except Exception as e:
				frappe.log_error(
					message=f"Error al actualizar current_occupancy del Shelf {self.shelf}: {str(e)}",
					title="Error en actualización de Shelf occupancy"
				)
		
		# Actualizar shelf destino (solo para Transferencias)
		if self.movement_type == "Transferencia" and self.to_shelf and frappe.db.exists("Shelf", self.to_shelf):
			try:
				# Forzar commit e invalidar caché también para el shelf destino
				frappe.db.commit()
				frappe.clear_cache(doctype="Bin")
				
				to_shelf_doc = frappe.get_doc("Shelf", self.to_shelf)
				to_shelf_doc.reload()
				
				if hasattr(to_shelf_doc, "calculate_current_occupancy"):
					new_occupancy = to_shelf_doc.calculate_current_occupancy()
					to_shelf_doc.current_occupancy = new_occupancy
					to_shelf_doc.save(ignore_permissions=True)
					frappe.db.commit()
			except Exception as e:
				frappe.log_error(
					message=f"Error al actualizar current_occupancy del Shelf destino {self.to_shelf}: {str(e)}",
					title="Error en actualización de Shelf occupancy"
				)

