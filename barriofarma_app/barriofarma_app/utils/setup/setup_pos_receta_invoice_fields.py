# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Expone custom_patient y custom_receta_medica en el POS (POS Settings → POS Additional Fields).

Sin esto, la caja ERPNext no muestra los campos farmaceuticos al pagar y el flujo
Receta Medica → POS Invoice + SII queda bloqueado en UI (validacion backend sigue activa).
"""

from __future__ import annotations

import frappe

POS_INVOICE_FIELDS = (
	"custom_patient",
	"custom_receta_medica",
)


def ensure_pos_receta_invoice_fields() -> list[str]:
	"""
	Idempotente: agrega filas faltantes en POS Settings.invoice_fields.

	Returns:
	    Lista de fieldnames agregados.
	"""
	added: list[str] = []
	settings = frappe.get_single("POS Settings")
	settings.invoice_type = "POS Invoice"

	existing = {row.fieldname for row in (settings.invoice_fields or [])}
	meta = frappe.get_meta("POS Invoice")

	for fieldname in POS_INVOICE_FIELDS:
		if fieldname in existing:
			continue
		field = meta.get_field(fieldname)
		if not field:
			frappe.logger().warning(
				"POS receta setup: campo %s no existe en POS Invoice; ejecute migrate",
				fieldname,
			)
			continue
		settings.append(
			"invoice_fields",
			{
				"fieldname": field.fieldname,
				"label": field.label,
				"fieldtype": field.fieldtype,
				"options": field.options,
				"reqd": 0,
				"read_only": 0,
			},
		)
		added.append(fieldname)

	if added:
		settings.save(ignore_permissions=True)
		frappe.db.commit()

	return added
