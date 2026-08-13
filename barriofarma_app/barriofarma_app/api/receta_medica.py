# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
API para Receta Medica (Story 5.3).
"""

import frappe
from frappe import _

from barriofarma_app.barriofarma_app.utils.domain.receta_medica_items import (
	get_receta_medica_items,
	add_receta_medica_items_to_invoice,
)
from barriofarma_app.barriofarma_app.utils.domain.receta_medica_dispensing import (
	get_receta_medica_pos_summary,
)


@frappe.whitelist()
def get_receta_medica_pos_summary_api(receta_name):
	"""Resumen de receta para panel del POS (medicamentos + saldos)."""
	return get_receta_medica_pos_summary(receta_name)


@frappe.whitelist()
def get_receta_medica_items_api(receta_name):
	"""
	Obtener items de una Receta Medica.
	"""
	return get_receta_medica_items(receta_name)


@frappe.whitelist()
def add_receta_medica_items_to_invoice_api(invoice_name, receta_name, warehouse=None):
	"""
	Agregar todos los items de una Receta Medica a una venta.
	"""
	return add_receta_medica_items_to_invoice(invoice_name, receta_name, warehouse)
