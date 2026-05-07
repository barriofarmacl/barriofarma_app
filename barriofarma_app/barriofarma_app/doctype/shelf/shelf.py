# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
DocType Shelf - Agregado DDD para gestión de estantes físicos
"""

import frappe
from frappe.model.document import Document
from frappe import _


class Shelf(Document):
	"""
	Agregado Shelf: Representa un estante físico dentro de un Warehouse
	"""
	
	def validate(self):
		"""
		Validar invariantes del dominio antes de guardar
		"""
		self.validate_warehouse()
		self.validate_warehouse_shelf_limit()
		self.validate_location_code_unique()
		self.validate_capacity()
		self.validate_shelf_type()

	def validate_warehouse_shelf_limit(self):
		"""
		Regla de negocio: un warehouse puede tener entre 0 y 10 estantes.

		Se valida al crear/editar Shelf para no exceder 10 registros por warehouse.
		"""
		if not self.warehouse:
			return

		existing_count = frappe.db.count(
			"Shelf",
			{
				"warehouse": self.warehouse,
				"name": ["!=", self.name],
			},
		)
		# +1 incluye el documento actual
		if int(existing_count or 0) + 1 > 10:
			frappe.throw(
				_("El almacén {0} ya tiene 10 estantes. No se pueden crear más.").format(
					frappe.bold(self.warehouse)
				),
				frappe.ValidationError,
			)
	
	def validate_warehouse(self):
		"""
		Invariante: Shelf debe pertenecer a un Warehouse válido y activo
		"""
		if not self.warehouse:
			frappe.throw(_("Warehouse es obligatorio"), frappe.MandatoryError)
		
		if not frappe.db.exists("Warehouse", self.warehouse):
			frappe.throw(_("Warehouse {0} no existe").format(self.warehouse), frappe.LinkValidationError)
		
		# Validar que el warehouse no esté deshabilitado
		warehouse_disabled = frappe.db.get_value("Warehouse", self.warehouse, "disabled")
		if warehouse_disabled:
			frappe.throw(_("No se puede crear Shelf en Warehouse deshabilitado: {0}").format(self.warehouse), frappe.ValidationError)
	
	def validate_location_code_unique(self):
		"""
		Invariante: location_code debe ser único dentro del mismo Warehouse
		"""
		if not self.location_code:
			frappe.throw(_("Código de Ubicación es obligatorio"), frappe.MandatoryError)
		
		# Buscar otros shelves con mismo location_code en mismo warehouse
		existing = frappe.db.get_value("Shelf", {
			"location_code": self.location_code,
			"warehouse": self.warehouse,
			"name": ["!=", self.name]
		}, "name")
		
		if existing:
			frappe.throw(
				_("Ya existe un estante con código '{0}' en el warehouse '{1}'").format(
					self.location_code, self.warehouse
				),
				frappe.DuplicateEntryError
			)
	
	def validate_capacity(self):
		"""
		Invariante: Validar capacidad según modo y estado
		"""
		# Si está en modo Fija, max_capacity es obligatorio
		if self.capacity_mode == "Fija" and not self.max_capacity:
			frappe.throw(_("Capacidad Máxima es obligatoria cuando Modo de Capacidad es 'Fija'"), frappe.MandatoryError)
		
		# Si está marcado como lleno y está en modo dinámica, establecer max_capacity
		if self.is_full and self.capacity_mode == "Dinámica":
			if not self.max_capacity:
				# Establecer max_capacity = current_occupancy si está disponible
				if self.current_occupancy:
					self.max_capacity = self.current_occupancy
		
		# Validar que si está lleno, la ocupación debe ser >= capacidad máxima
		if self.is_full and self.max_capacity:
			if self.current_occupancy and self.current_occupancy < self.max_capacity:
				frappe.throw(
					_("No se puede marcar como lleno: ocupación actual ({0}) es menor que capacidad máxima ({1})").format(
						self.current_occupancy, self.max_capacity
					),
					frappe.ValidationError
				)
	
	def validate_shelf_type(self):
		"""
		Invariante: Validar que shelf_type sea válido
		"""
		valid_types = ["Normal", "Refrigerado", "Controlado", "Mostrador"]
		if self.shelf_type and self.shelf_type not in valid_types:
			frappe.throw(
				_("Tipo de Estante inválido: {0}. Debe ser uno de: {1}").format(
					self.shelf_type, ", ".join(valid_types)
				),
				frappe.ValidationError
			)
	
	def calculate_current_occupancy(self):
		"""
		Calcular ocupación actual del estante desde stock real (Bin)
		Suma el stock (actual_qty) de todos los items que tienen este shelf 
		en su custom_shelf_locations dentro del warehouse del shelf
		"""
		if not self.warehouse:
			return 0.0
		
		# Buscar todos los items que tienen este shelf en custom_shelf_locations
		items_in_shelf = frappe.db.sql("""
			SELECT DISTINCT parent
			FROM `tabItem Shelf Location`
			WHERE shelf = %s
		""", (self.name,), as_dict=True)
		
		if not items_in_shelf:
			return 0.0
		
		# Obtener códigos de items
		item_codes = [item.parent for item in items_in_shelf]
		
		if not item_codes:
			return 0.0
		
		# Sumar el stock (actual_qty) de estos items en el warehouse del shelf
		total_stock = frappe.db.sql("""
			SELECT SUM(actual_qty) as total
			FROM `tabBin`
			WHERE item_code IN %s
			AND warehouse = %s
		""", (item_codes, self.warehouse), as_dict=True)
		
		if total_stock and total_stock[0].get("total"):
			return float(total_stock[0].get("total"))
		
		return 0.0
	
	def on_update(self):
		"""
		Actualizar ocupación actual después de guardar
		"""
		# Calcular y actualizar ocupación actual desde stock real
		self.current_occupancy = self.calculate_current_occupancy()

