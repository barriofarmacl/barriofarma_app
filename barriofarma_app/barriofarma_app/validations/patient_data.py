# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Validación de datos mínimos de cliente/paciente según normativa chilena.

FR26: El sistema debe registrar datos mínimos del cliente/paciente según normativa chilena
"""

import frappe
from frappe import _
from barriofarma_app.barriofarma_app.utils.rut_validation import validate_rut_format


def validate_patient_data_required(doc, method=None):
	"""
	Valida que se registren datos mínimos del cliente/paciente según normativa chilena.
	
	Según normativa chilena, para medicamentos controlados (Psicotrópico, Estupefaciente)
	o que requieren receta, se debe registrar:
	- Nombre completo del cliente/paciente
	- RUT (si es requerido)
	
	Args:
		doc: Sales Invoice o POS Invoice
		method: Método del hook (opcional)
	"""
	if not doc.get("items"):
		return
	
	# Verificar si algún item requiere datos de paciente
	requires_patient_data = False
	items_requiring_data = []
	
	for item in doc.items:
		if not item.item_code:
			continue
		
		try:
			item_doc = frappe.get_doc("Item", item.item_code)
			
			# Verificar si el medicamento requiere datos de paciente
			# Según normativa: medicamentos controlados o que requieren receta
			control_level = item_doc.get("custom_control_level")
			requires_prescription = item_doc.get("custom_requires_prescription_retention", 0)
			
			if control_level in ["Psicotrópico", "Estupefaciente"] or requires_prescription:
				requires_patient_data = True
				items_requiring_data.append({
					"item_code": item.item_code,
					"item_name": item.item_name or item.item_code,
					"control_level": control_level,
					"requires_prescription": requires_prescription
				})
		except frappe.DoesNotExistError:
			# Si el item no existe, no podemos validar
			continue
		except Exception as e:
			frappe.log_error(
				message=f"Error al consultar item {item.item_code} para validación de datos de paciente: {str(e)}",
				title="Error en Validación de Datos de Paciente"
			)
			continue
	
	# Si no hay items que requieran datos de paciente, no validar
	if not requires_patient_data:
		return
	
	# Obtener Customer
	customer_name = doc.get("customer")
	if not customer_name:
		frappe.throw(
			_("Se requiere un cliente para productos que necesitan datos de paciente según normativa chilena."),
			title=_("Cliente Requerido")
		)
	
	try:
		customer = frappe.get_doc("Customer", customer_name)
	except frappe.DoesNotExistError:
		frappe.throw(
			_("El cliente {0} no existe.").format(frappe.bold(customer_name)),
			title=_("Cliente No Encontrado")
		)
	
	# Validar nombre completo
	if not customer.get("customer_name") or not customer.customer_name.strip():
		frappe.throw(
			_("El cliente debe tener un nombre completo registrado para productos que requieren datos de paciente según normativa chilena."),
			title=_("Nombre de Cliente Requerido")
		)
	
	# Validar RUT si está presente
	customer_rut = customer.get("custom_rut")
	if customer_rut:
		is_valid, cleaned_rut, error_message = validate_rut_format(customer_rut)
		if not is_valid:
			frappe.throw(
				_("El RUT del cliente {0} tiene formato inválido: {1}").format(
					frappe.bold(customer_name),
					error_message
				),
				title=_("RUT Inválido")
			)
	
	# Advertencia si no hay RUT pero se requiere (según normativa, RUT puede ser opcional en algunos casos)
	# Por ahora, solo validamos que el nombre esté presente
	# El RUT es recomendado pero no siempre obligatorio según normativa

