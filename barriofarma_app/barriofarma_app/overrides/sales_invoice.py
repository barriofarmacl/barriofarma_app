# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Override del DocType Sales Invoice para registrar automáticamente Shelf Movement
al realizar ventas desde estantes específicos
"""

import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as ERPNextSalesInvoice
from datetime import datetime


class SalesInvoice(ERPNextSalesInvoice):
	"""
	Extensión de la clase Sales Invoice de ERPNext para registrar
	automáticamente movimientos de tipo "Venta" en Shelf Movement
	cuando se venden productos desde estantes específicos
	"""
	
	def on_submit(self):
		"""
		Registrar Shelf Movement automáticamente cuando se envía Sales Invoice
		"""
		super().on_submit()
		self.create_shelf_movements_from_sale()
	
	def create_shelf_movements_from_sale(self):
		"""
		Crear registros de Shelf Movement tipo "Venta" basados en los items vendidos
		"""
		if not self.items:
			return
		
		for item in self.items:
			item_code = item.item_code
			warehouse = item.warehouse or self.set_warehouse
			quantity = item.qty
			
			if not item_code or not warehouse:
				continue
			
			# Obtener shelves del item en el warehouse de la venta
			shelves = self._get_item_shelves_in_warehouse(item_code, warehouse)
			
			# Si el item tiene shelves asignados, crear movimiento de venta para cada shelf
			# Distribuir la cantidad proporcionalmente o usar el primer shelf
			if shelves:
				# Por ahora, usar el primer shelf disponible para simplificar
				# En el futuro se podría implementar lógica más sofisticada
				primary_shelf = shelves[0]
				self._create_shelf_movement_venta(
					shelf=primary_shelf,
					item_code=item_code,
					quantity=quantity
				)
	
	def _get_item_shelves_in_warehouse(self, item_code, warehouse):
		"""
		Obtener lista de shelves donde está asignado el item en el warehouse especificado
		
		Args:
			item_code: Código del item
			warehouse: Nombre del warehouse
		
		Returns:
			Lista de nombres de shelves
		"""
		if not frappe.db.exists("Item", item_code):
			return []
		
		item_doc = frappe.get_doc("Item", item_code)
		
		# Verificar si el item tiene custom_shelf_locations
		if not hasattr(item_doc, "custom_shelf_locations") or not item_doc.custom_shelf_locations:
			return []
		
		shelves = []
		for shelf_location in item_doc.custom_shelf_locations:
			shelf_name = shelf_location.get("shelf")
			if shelf_name and frappe.db.exists("Shelf", shelf_name):
				# Verificar que el shelf pertenece al warehouse de la venta
				shelf_doc = frappe.get_doc("Shelf", shelf_name)
				if shelf_doc.warehouse == warehouse:
					shelves.append(shelf_name)
		
		return shelves
	
	def _create_shelf_movement_venta(self, shelf, item_code, quantity):
		"""
		Crear registro de Shelf Movement tipo "Venta"
		
		Args:
			shelf: Nombre del shelf
			item_code: Código del item
			quantity: Cantidad vendida
		"""
		try:
			movement = frappe.get_doc({
				"doctype": "Shelf Movement",
				"movement_type": "Venta",
				"shelf": shelf,
				"item": item_code,
				"quantity": quantity,
				"movement_date": self.posting_date or datetime.now(),
				"reference_doctype": "Sales Invoice",
				"reference_name": self.name,
				"notes": f"Movimiento automático desde Sales Invoice {self.name}"
			})
			
			movement.insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(
				message=f"Error al crear Shelf Movement desde Sales Invoice {self.name}: {str(e)}",
				title="Error en Shelf Movement"
			)
			# No lanzar excepción para no bloquear el submit del Sales Invoice
			# pero registrar el error para debugging

