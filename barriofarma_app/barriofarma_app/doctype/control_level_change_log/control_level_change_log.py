# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
DocType: Control Level Change Log

Story 1.4: Auditoría de Cambios en Control Level

Este DocType registra todos los cambios en el nivel de control (custom_control_level)
de medicamentos, proporcionando una auditoría completa e inmutable para cumplimiento
normativo (FR25, FR40).

Características:
- Registro inmutable: No se puede modificar ni eliminar después de crear
- Motivo obligatorio: Requiere razón documentada para cada cambio
- Trazabilidad completa: Registra usuario, fecha/hora, valores anterior/nuevo
- Referencia opcional: Puede vincularse a Sales Invoice u otro documento
"""

import frappe
from frappe import _
from frappe.model.document import Document


class ControlLevelChangeLog(Document):
	"""
	Registro de auditoría para cambios en control level de medicamentos.
	
	Este DocType es de solo lectura después de crear (inmutable) para garantizar
	la integridad de la auditoría.
	"""
	
	def validate(self):
		"""
		Validar que el motivo esté presente y que el registro sea válido.
		
		Nota: Este método se ejecuta antes de insertar el documento.
		Una vez insertado, el documento no puede modificarse (write=0 en permisos).
		"""
		if not self.reason or not self.reason.strip():
			frappe.throw(
				_("El motivo del cambio (reason) es obligatorio. Debe documentar por qué se cambió el nivel de control del medicamento."),
				title=_("Motivo Requerido")
			)
		
		if not self.item_code:
			frappe.throw(
				_("El código del item (item_code) es obligatorio."),
				title=_("Item Requerido")
			)
		
		# Validar que el item existe
		if not frappe.db.exists("Item", self.item_code):
			frappe.throw(
				_("El item '{0}' no existe.").format(frappe.bold(self.item_code)),
				title=_("Item Inválido")
			)
	
	def before_insert(self):
		"""
		Establecer valores automáticos antes de insertar.
		"""
		# Establecer usuario actual si no está definido
		if not self.changed_by:
			self.changed_by = frappe.session.user
		
		# Establecer fecha/hora actual si no está definida
		if not self.changed_on:
			from frappe.utils import now
			self.changed_on = now()
	
	def on_update(self):
		"""
		Prevenir modificaciones después de crear.
		
		Nota: Los permisos ya previenen write=0, pero esta validación adicional
		proporciona una capa extra de seguridad.
		"""
		if self.docstatus == 1:  # Si ya está submitted
			frappe.throw(
				_("Los registros de auditoría de cambios en control level no pueden modificarse después de crearse. Este registro es inmutable para garantizar la integridad de la auditoría."),
				title=_("Registro Inmutable")
			)

