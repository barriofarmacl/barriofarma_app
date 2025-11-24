# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Override del DocType Stock Entry para registrar automáticamente Shelf Movement
"""

import frappe
from frappe import _
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry as ERPNextStockEntry
from datetime import datetime


class StockEntry(ERPNextStockEntry):
	"""
	Extensión de la clase Stock Entry de ERPNext para registrar
	automáticamente movimientos en Shelf Movement y validar capacidad/tipo de estante
	"""
	
	def validate(self):
		"""
		Validar capacidad y tipo de estante antes de guardar/enviar
		"""
		super().validate()
		# Solo validar si el documento está siendo enviado (docstatus == 0 y tiene items con shelves)
		if self.docstatus == 0 and self.items:
			self.validate_shelf_capacity_and_type()
	
	def on_submit(self):
		"""
		Registrar Shelf Movement automáticamente cuando se envía Stock Entry
		"""
		super().on_submit()
		self.create_shelf_movements()
	
	def validate_shelf_capacity_and_type(self):
		"""
		Validar capacidad y tipo de estante para cada item
		"""
		if not self.items:
			return
		
		for item in self.items:
			from_shelf = item.get("custom_from_shelf")
			to_shelf = item.get("custom_to_shelf")
			
			# Validar shelf destino si existe
			if to_shelf:
				self._validate_shelf_capacity(to_shelf, item.item_code, item.qty)
				self._validate_shelf_item_compatibility(to_shelf, item.item_code)
			
			# Validar shelf origen si existe (para transferencias)
			if from_shelf:
				self._validate_shelf_item_compatibility(from_shelf, item.item_code)
	
	def _validate_shelf_capacity(self, shelf_name, item_code, quantity):
		"""
		Validar que el shelf tiene capacidad suficiente
		"""
		if not frappe.db.exists("Shelf", shelf_name):
			return
		
		shelf_doc = frappe.get_doc("Shelf", shelf_name)
		
		if shelf_doc.max_capacity:
			current_occupancy = shelf_doc.calculate_current_occupancy()
			available_capacity = shelf_doc.max_capacity - current_occupancy
			
			if quantity > available_capacity:
				frappe.throw(
					_("No se puede agregar {0} unidades del producto {1} al estante {2}: "
					  "el stock del producto ({3}) excede la capacidad disponible ({4}) "
					  "del estante (capacidad máxima: {5}, ocupación actual: {6})").format(
						quantity,
						frappe.bold(item_code),
						frappe.bold(shelf_doc.shelf_name),
						quantity,
						available_capacity,
						shelf_doc.max_capacity,
						current_occupancy
					),
					title=_("Capacidad del Estante Excedida")
				)
	
	def _validate_shelf_item_compatibility(self, shelf_name, item_code):
		"""
		Validar que el tipo de estante es compatible con el producto
		"""
		if not frappe.db.exists("Shelf", shelf_name) or not frappe.db.exists("Item", item_code):
			return
		
		shelf_doc = frappe.get_doc("Shelf", shelf_name)
		item_doc = frappe.get_doc("Item", item_code)
		
		shelf_type = shelf_doc.get("shelf_type")
		
		# Validar estante Refrigerado
		if shelf_type == "Refrigerado":
			requires_refrigeration = item_doc.get("custom_requires_refrigeration")
			if not requires_refrigeration:
				frappe.throw(
					_("El estante {0} es de tipo Refrigerado y solo puede contener productos que requieren refrigeración. "
					  "El producto {1} no requiere refrigeración.").format(
						frappe.bold(shelf_doc.shelf_name),
						frappe.bold(item_code)
					),
					title=_("Incompatibilidad Tipo Estante-Producto")
				)
		
		# Validar estante Controlado
		if shelf_type == "Controlado":
			control_level = item_doc.get("custom_control_level")
			if not control_level or control_level == "None":
				frappe.throw(
					_("El estante {0} es de tipo Controlado y solo puede contener productos con nivel de control "
					  "(Psicotrópico o Estupefaciente). El producto {1} no tiene nivel de control.").format(
						frappe.bold(shelf_doc.shelf_name),
						frappe.bold(item_code)
					),
					title=_("Incompatibilidad Tipo Estante-Producto")
				)
	
	def create_shelf_movements(self):
		"""
		Crear registros de Shelf Movement basados en los items del Stock Entry
		"""
		if not self.items:
			return
		
		for item in self.items:
			# Determinar tipo de movimiento según stock_entry_type
			movement_type = self._get_movement_type()
			
			# Obtener shelves desde campos custom
			from_shelf = item.get("custom_from_shelf")
			to_shelf = item.get("custom_to_shelf")
			
			# Solo crear movimiento si hay al menos un shelf especificado
			if not from_shelf and not to_shelf:
				continue
			
			# Determinar shelf principal según tipo de movimiento
			if movement_type == "Transferencia":
				# Transferencia requiere ambos shelves
				if from_shelf and to_shelf:
					self._create_shelf_movement(
						movement_type=movement_type,
						shelf=from_shelf,
						to_shelf=to_shelf,
						item=item.item_code,
						quantity=item.qty
					)
			elif movement_type == "Recepción":
				# Recepción solo requiere shelf destino
				if to_shelf:
					self._create_shelf_movement(
						movement_type=movement_type,
						shelf=to_shelf,
						item=item.item_code,
						quantity=item.qty
					)
			elif movement_type == "Venta":
				# Venta requiere shelf origen
				if from_shelf:
					self._create_shelf_movement(
						movement_type=movement_type,
						shelf=from_shelf,
						item=item.item_code,
						quantity=item.qty
					)
			elif movement_type == "Ajuste":
				# Ajuste puede tener shelf origen o destino
				shelf = from_shelf or to_shelf
				if shelf:
					self._create_shelf_movement(
						movement_type=movement_type,
						shelf=shelf,
						item=item.item_code,
						quantity=item.qty
					)
	
	def _get_movement_type(self):
		"""
		Determinar tipo de movimiento según stock_entry_type
		"""
		stock_entry_type = self.stock_entry_type
		
		type_mapping = {
			"Material Transfer": "Transferencia",
			"Material Receipt": "Recepción",
			"Material Issue": "Venta",
			"Material Transfer for Manufacture": "Transferencia",
			"Manufacture": "Ajuste",
			"Repack": "Ajuste",
			"Send to Subcontractor": "Transferencia",
			"Send to Warehouse": "Transferencia",
			"Receive at Warehouse": "Recepción"
		}
		
		return type_mapping.get(stock_entry_type, "Ajuste")
	
	def _create_shelf_movement(self, movement_type, shelf, item, quantity, to_shelf=None):
		"""
		Crear registro de Shelf Movement
		"""
		try:
			movement = frappe.get_doc({
				"doctype": "Shelf Movement",
				"movement_type": movement_type,
				"shelf": shelf,
				"to_shelf": to_shelf,
				"item": item,
				"quantity": quantity,
				"movement_date": self.posting_date or datetime.now(),
				"reference_doctype": "Stock Entry",
				"reference_name": self.name,
				"notes": f"Movimiento automático desde Stock Entry {self.name}"
			})
			
			movement.insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(
				message=f"Error al crear Shelf Movement desde Stock Entry {self.name}: {str(e)}",
				title="Error en Shelf Movement"
			)
			# No lanzar excepción para no bloquear el submit del Stock Entry
			# pero registrar el error para debugging

