# -*- coding: utf-8 -*-
"""Sincroniza Custom Fields de estantes en Stock Entry Detail (grid visible)."""
import frappe


def sync_stock_entry_shelf_grid_fields():
	updates = {
		"Stock Entry Detail-custom_from_shelf": {
			"in_list_view": 1,
			"columns": 2,
			"insert_after": "s_warehouse",
		},
		"Stock Entry Detail-custom_to_shelf": {
			"in_list_view": 1,
			"columns": 2,
			"insert_after": "t_warehouse",
		},
	}
	changed = []
	for name, values in updates.items():
		if not frappe.db.exists("Custom Field", name):
			continue
		doc = frappe.get_doc("Custom Field", name)
		for key, val in values.items():
			setattr(doc, key, val)
		doc.flags.ignore_validate = True
		doc.save(ignore_permissions=True)
		changed.append(name)

	if changed:
		frappe.db.commit()
		frappe.clear_cache(doctype="Stock Entry Detail")

	return changed
