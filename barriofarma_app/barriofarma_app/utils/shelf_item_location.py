# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Utilidades para vincular items a estantes (Item Shelf Location)."""

from __future__ import annotations

import frappe
from frappe.utils import flt


def link_item_to_shelf(item_code: str, shelf: str, quantity: float | None = None) -> bool:
	"""
	Agrega fila en custom_shelf_locations si el item aún no está vinculado al estante.
	Retorna True si se creó o actualizó el vínculo.
	"""
	if not item_code or not shelf or not frappe.db.exists("Item", item_code):
		return False
	if not frappe.db.exists("Shelf", shelf):
		return False

	item_doc = frappe.get_doc("Item", item_code)
	if not hasattr(item_doc, "custom_shelf_locations"):
		return False

	existing = {r.shelf for r in (item_doc.custom_shelf_locations or []) if r.shelf}
	if shelf in existing:
		return False

	item_doc.append(
		"custom_shelf_locations",
		{
			"shelf": shelf,
			"preferred_location": 0 if existing else 1,
			"quantity": flt(quantity),
		},
	)
	item_doc.save(ignore_permissions=True)
	return True
