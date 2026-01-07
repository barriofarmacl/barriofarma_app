# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Validación de disponibilidad de stock en tiempo real para ventas.

FR22: El sistema debe validar disponibilidad de stock antes de permitir una venta
"""

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.stock.utils import get_or_make_bin


def validate_stock_availability(doc, method=None):
	"""
	Valida que hay stock disponible antes de permitir una venta.
	
	Para cada item en la venta:
	- Consulta Bin.actual_qty para stock disponible en el warehouse
	- Valida que cantidad solicitada <= stock disponible
	- Muestra advertencia si stock es bajo (< stock mínimo)
	- Previene venta si stock es 0 o negativo o cantidad > stock disponible
	
	Args:
		doc: Sales Invoice o POS Invoice
		method: Método del hook (opcional)
	"""
	if not doc.get("items"):
		return
	
	for item in doc.items:
		if not item.item_code:
			continue
		
		# Obtener warehouse del item o del documento
		warehouse = item.warehouse or doc.set_warehouse
		if not warehouse:
			# Si no hay warehouse, no podemos validar stock
			# ERPNext manejará esto en su validación estándar
			continue
		
		# Obtener cantidad solicitada
		requested_qty = flt(item.qty)
		if requested_qty <= 0:
			continue
		
		# Obtener stock disponible del Bin
		try:
			bin_name = get_or_make_bin(item.item_code, warehouse)
			bin_doc = frappe.get_doc("Bin", bin_name)
			available_qty = flt(bin_doc.actual_qty or 0)
		except Exception as e:
			frappe.log_error(
				message=f"Error al consultar stock para item {item.item_code} en warehouse {warehouse}: {str(e)}",
				title="Error en Validación de Stock"
			)
			# Si hay error al consultar stock, no bloqueamos la venta
			# pero registramos el error
			continue
		
		# Validar que hay stock suficiente
		if available_qty <= 0:
			frappe.throw(
				_("El producto {0} no tiene stock disponible en el almacén {1} (stock actual: {2}). No se puede realizar la venta.").format(
					frappe.bold(item.item_code),
					frappe.bold(warehouse),
					available_qty
				),
				title=_("Stock No Disponible")
			)
			return  # No continuar con validaciones adicionales si no hay stock
		
		if requested_qty > available_qty:
			frappe.throw(
				_("Stock insuficiente para el producto {0} en el almacén {1}. Cantidad solicitada: {2}, Stock disponible: {3}.").format(
					frappe.bold(item.item_code),
					frappe.bold(warehouse),
					requested_qty,
					available_qty
				),
				title=_("Stock Insuficiente")
			)
		
		# Advertencia si stock es bajo (menor que stock mínimo)
		try:
			item_doc = frappe.get_doc("Item", item.item_code)
			stock_minimum = flt(item_doc.get("stock_minimum") or 0)
			
			if stock_minimum > 0 and available_qty < stock_minimum:
				frappe.msgprint(
					_("Advertencia: El producto {0} tiene stock bajo en el almacén {1}. Stock actual: {2}, Stock mínimo: {3}.").format(
						frappe.bold(item.item_code),
						frappe.bold(warehouse),
						available_qty,
						stock_minimum
					),
					indicator="orange",
					title=_("Stock Bajo")
				)
		except frappe.DoesNotExistError:
			# Si el item no existe, no podemos verificar stock mínimo
			pass
		except Exception as e:
			# Si hay error al consultar item, no bloqueamos pero registramos
			frappe.log_error(
				message=f"Error al consultar stock mínimo para item {item.item_code}: {str(e)}",
				title="Error en Validación de Stock Mínimo"
			)

