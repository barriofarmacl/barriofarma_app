# -*- coding: utf-8 -*-
"""
Renombra columna custom_prescription -> custom_receta_medica en Sales Invoice y POS Invoice,
y actualiza registros en tabCustom Field (Prescription -> Receta Medica naming plan).
"""

import frappe


def execute():
	if frappe.flags.in_install or frappe.flags.in_uninstall:
		return

	for dt in ("Sales Invoice", "POS Invoice"):
		table = f"tab{dt}"
		try:
			columns = frappe.db.get_table_columns(dt)
		except Exception:
			continue

		if "custom_receta_medica" in columns:
			continue
		if "custom_prescription" not in columns:
			continue

		frappe.db.sql_ddl(
			f"ALTER TABLE `{table}` CHANGE COLUMN `custom_prescription` `custom_receta_medica` VARCHAR(140)"
		)

	old_names = ("Sales Invoice-custom_prescription", "POS Invoice-custom_prescription")
	for old in old_names:
		if not frappe.db.exists("Custom Field", old):
			continue
		new = old.replace("custom_prescription", "custom_receta_medica")
		if frappe.db.exists("Custom Field", new):
			# Ya existe el CF con el nombre nuevo (p. ej. fixtures); quitar fila legada sin choque de PK.
			frappe.db.sql("DELETE FROM `tabCustom Field` WHERE name=%s", (old,))
			continue
		frappe.db.sql(
			"""
			UPDATE `tabCustom Field`
			SET name=%(new)s, fieldname=%(fn)s, modified=%(mod)s
			WHERE name=%(old)s
			""",
			{"new": new, "fn": "custom_receta_medica", "old": old, "mod": frappe.utils.now()},
		)

	frappe.db.commit()
	frappe.clear_cache(doctype="Sales Invoice")
	frappe.clear_cache(doctype="POS Invoice")
