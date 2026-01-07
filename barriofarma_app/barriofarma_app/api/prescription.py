# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
API endpoints para funcionalidad de recetas

Story 5.3: Asociación de Receta a Múltiples Medicamentos
"""

import frappe
from frappe import _
from barriofarma_app.barriofarma_app.utils.prescription_items import (
	get_prescription_items,
	add_prescription_items_to_invoice
)


@frappe.whitelist()
def get_prescription_items_api(prescription_name):
	"""
	API endpoint para obtener items de una receta.
	
	Args:
		prescription_name: Nombre de la receta (Prescription)
	
	Returns:
		Lista de items de la receta
	"""
	return get_prescription_items(prescription_name)


@frappe.whitelist()
def add_prescription_items_to_invoice_api(invoice_name, prescription_name, warehouse=None):
	"""
	API endpoint para agregar todos los items de una receta a una venta.
	
	Args:
		invoice_name: Nombre de la venta (Sales Invoice o POS Invoice)
		prescription_name: Nombre de la receta (Prescription)
		warehouse: Warehouse opcional para los items
	
	Returns:
		Información sobre los items agregados
	"""
	return add_prescription_items_to_invoice(invoice_name, prescription_name, warehouse)

