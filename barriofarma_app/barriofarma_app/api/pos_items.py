# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Enriquece items del POS con flags de dispensacion (receta retenida)."""

from __future__ import annotations

import frappe
from frappe.utils import cint

from erpnext.selling.page.point_of_sale.point_of_sale import get_items as erpnext_get_items

RECETA_RETENIDA = "Venta con Receta Retenida"


def enrich_pos_items(items: list[dict] | None) -> list[dict]:
	if not items:
		return []

	codes = list({row.get("item_code") for row in items if isinstance(row, dict) and row.get("item_code")})
	if not codes:
		return list(items)

	meta_rows = frappe.get_all(
		"Item",
		filters={"name": ["in", codes]},
		fields=["name", "custom_dispensing_type", "custom_requires_prescription_retention"],
	)
	by_code = {row["name"]: row for row in meta_rows}

	for item in items:
		if not isinstance(item, dict):
			continue
		row = by_code.get(item.get("item_code"), {})
		dispensing_type = row.get("custom_dispensing_type") or ""
		requires_retention = cint(row.get("custom_requires_prescription_retention"))
		item["custom_dispensing_type"] = dispensing_type
		item["custom_requires_prescription_retention"] = requires_retention
		item["requires_receta_retenida"] = int(
			dispensing_type == RECETA_RETENIDA or requires_retention
		)

	return items


def _enrich_get_items_response(result):
	"""ERPNext v16 devuelve dict {items: []} salvo busqueda directa (lista)."""
	if isinstance(result, dict) and "items" in result:
		result["items"] = enrich_pos_items(result.get("items") or [])
		return result
	if isinstance(result, list):
		return enrich_pos_items(result)
	return result


@frappe.whitelist()
def get_items(start, page_length, price_list, item_group, pos_profile, search_term=""):
	result = erpnext_get_items(start, page_length, price_list, item_group, pos_profile, search_term)
	return _enrich_get_items_response(result)
