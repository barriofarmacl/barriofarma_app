# -*- coding: utf-8 -*-
"""
Backfill custom_requires_prescription_retention / custom_prescription_storage_required
from custom_dispensing_type (whiteboard #78 PR5).

Rules:
- RR -> retention=1, storage=1
- VL + control None -> retention=0, storage=0
- VL + Psico/Estupe -> retention=1, storage=0 (log for manual dispensing fix)
"""

import frappe


def execute():
	if frappe.flags.in_install or frappe.flags.in_uninstall:
		return

	rr_items = frappe.get_all(
		"Item",
		filters={"custom_dispensing_type": "Venta con Receta Retenida"},
		pluck="name",
	)
	for name in rr_items:
		frappe.db.set_value(
			"Item",
			name,
			{
				"custom_requires_prescription_retention": 1,
				"custom_prescription_storage_required": 1,
			},
			update_modified=False,
		)

	vl_items = frappe.get_all(
		"Item",
		filters={"custom_dispensing_type": "Venta Libre"},
		fields=["name", "custom_control_level"],
	)
	controlled_mismatch = []
	for row in vl_items:
		control = row.get("custom_control_level")
		if control in ("Psicotrópico", "Estupefaciente"):
			frappe.db.set_value(
				"Item",
				row.name,
				{"custom_requires_prescription_retention": 1, "custom_prescription_storage_required": 0},
				update_modified=False,
			)
			controlled_mismatch.append(row.name)
		else:
			frappe.db.set_value(
				"Item",
				row.name,
				{"custom_requires_prescription_retention": 0, "custom_prescription_storage_required": 0},
				update_modified=False,
			)

	frappe.db.commit()
	frappe.clear_cache(doctype="Item")

	if controlled_mismatch:
		frappe.logger("barriofarma_app").warning(
			"PR5 sync_item_dispensing_retention_flags: %s Item(s) Venta Libre con control "
			"Psicotrópico/Estupefaciente — retention=1 forzado; revisar Tipo de Dispensación en Desk: %s",
			len(controlled_mismatch),
			", ".join(controlled_mismatch[:20])
			+ ("..." if len(controlled_mismatch) > 20 else ""),
		)
