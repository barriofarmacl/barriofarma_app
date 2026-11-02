# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Turno de atención en el local físico.

Issue whiteboard #90 - change SDD barriofarma-turnos-atencion

El turno representa orden de llegada, no una transacción comercial: no
referencia documentos de venta ni registra identidad del cliente. Esa frontera
es deliberada y está cubierta por el escenario S17 del spec.

La unicidad de `(fecha, numero)` no se valida en Python. Vive en el `autoname`
`format:TRN-{fecha}-{numero}`, que la convierte en la clave primaria: la base
de datos rechaza el duplicado con `DuplicateEntryError` incluso bajo emisión
concurrente, que es justo el modo de falla que importa.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

ESTADO_INICIAL = "Esperando"
ESTADOS_ABIERTOS = ("Esperando", "Llamado")
ESTADOS_CERRADOS = ("Atendido", "Ausente")


class TurnoAtencion(Document):
	def before_insert(self):
		if not self.estado:
			self.estado = ESTADO_INICIAL
		if not self.emitido_en:
			self.emitido_en = now_datetime()

	def validate(self):
		if not self.numero or self.numero < 1:
			frappe.throw(_("El número de turno debe ser positivo."))

		if self.estado in ESTADOS_CERRADOS and not self.cerrado_en:
			self.cerrado_en = now_datetime()
