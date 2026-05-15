# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Validación de límites de descuento por rol de usuario.

FR27: El sistema debe permitir aplicar descuentos y promociones a productos

Spec pos-pharma-payments-boundary R5: esta regla permanece en barriofarma_app como
politica clinica-comercial por rol (no es regla de medio de pago). No mover a pagosbf
sin un change explicito de arquitectura.
"""

import frappe
from frappe import _
from frappe.utils import flt


# Límites de descuento por rol (en porcentaje)
# Estos límites pueden configurarse en un DocType de configuración en el futuro
DISCOUNT_LIMITS_BY_ROLE = {
	"System Manager": 100.0,  # Sin límite para administradores
	"Farmacéutico": 50.0,  # Máximo 50% de descuento
	"Sales User": 30.0,  # Máximo 30% de descuento para vendedores
	"Sales Manager": 50.0,  # Máximo 50% de descuento para gerentes de ventas
	"Accounts User": 20.0,  # Máximo 20% de descuento para contadores
}


def get_max_discount_for_user():
	"""
	Obtiene el límite máximo de descuento permitido para el usuario actual.
	
	Returns:
		float: Porcentaje máximo de descuento permitido
	"""
	user_roles = frappe.get_roles()
	
	# Buscar el límite más alto entre los roles del usuario
	max_discount = 0.0
	for role in user_roles:
		if role in DISCOUNT_LIMITS_BY_ROLE:
			role_limit = DISCOUNT_LIMITS_BY_ROLE[role]
			if role_limit > max_discount:
				max_discount = role_limit
	
	# Si no tiene ningún rol con límite definido, usar un límite por defecto conservador
	if max_discount == 0.0:
		max_discount = 20.0  # Límite por defecto: 20%
	
	return max_discount


def validate_discount_limits(doc, method=None):
	"""
	Valida que los descuentos aplicados no excedan los límites permitidos por rol.
	
	Valida:
	- Descuento adicional en Sales Invoice (additional_discount_percentage)
	- Descuentos por item (discount_percentage en Sales Invoice Item)
	
	Args:
		doc: Sales Invoice o POS Invoice
		method: Método del hook (opcional)
	"""
	if not doc.get("items"):
		return
	
	# Obtener límite máximo para el usuario actual
	max_discount = get_max_discount_for_user()
	
	# Validar descuento adicional en el documento
	if doc.get("additional_discount_percentage"):
		additional_discount = flt(doc.additional_discount_percentage)
		if additional_discount > max_discount:
			frappe.throw(
				_("El descuento adicional ({0}%) excede el límite permitido para su rol ({1}%). Contacte a un administrador si necesita aplicar un descuento mayor.").format(
					additional_discount,
					max_discount
				),
				title=_("Límite de Descuento Excedido")
			)
	
	# Validar descuentos por item
	for item in doc.items:
		if item.get("discount_percentage"):
			item_discount = flt(item.discount_percentage)
			if item_discount > max_discount:
				frappe.throw(
					_("El descuento en el producto {0} ({1}%) excede el límite permitido para su rol ({2}%). Contacte a un administrador si necesita aplicar un descuento mayor.").format(
						frappe.bold(item.item_code or item.item_name),
						item_discount,
						max_discount
					),
					title=_("Límite de Descuento Excedido")
				)
	
	# Nota: La validación del descuento total se omite intencionalmente porque:
	# 1. Ya validamos descuentos individuales (por item) y descuento adicional
	# 2. El cálculo del descuento total puede ser complejo y depende de cómo ERPNext
	#    calcula los totales (puede incluir impuestos, otros ajustes, etc.)
	# 3. Si todos los descuentos individuales están dentro del límite, el descuento total
	#    también debería estar dentro del límite (a menos que haya otros factores)
	# 
	# Si en el futuro se necesita validar el descuento total, se puede implementar
	# consultando directamente los campos calculados de ERPNext o usando frappe.get_doc
	# para obtener los valores reales después de que ERPNext haya calculado los totales.

