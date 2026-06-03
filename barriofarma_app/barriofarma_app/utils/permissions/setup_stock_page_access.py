# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Página Desk ``stock-balance`` (Resumen de existencia / Stock Summary).

Solo tenía rol Stock User; sin acceso la auxiliar no ve Move/Agregar ni filtros.
"""

import frappe

from barriofarma_app.barriofarma_app.utils.permissions.setup_pos_page_access import (
	BARRIOFARMA_POS_PAGE_ROLES,
)

STOCK_BALANCE_PAGE = "stock-balance"

# Mismos roles operativos que POS (Farmacéutico, Auxiliar)
STOCK_PAGE_ROLES = BARRIOFARMA_POS_PAGE_ROLES


def setup_stock_balance_page_roles():
	"""Idempotente: roles BarrioFarma en Page stock-balance."""
	if not frappe.db.exists("Page", STOCK_BALANCE_PAGE):
		frappe.logger().warning("Page %s no existe; se omite", STOCK_BALANCE_PAGE)
		return []

	added = []
	page = frappe.get_doc("Page", STOCK_BALANCE_PAGE)
	existing = {row.role for row in page.roles}

	for role in STOCK_PAGE_ROLES:
		if role not in existing:
			page.append("roles", {"role": role})
			added.append(role)

	if added:
		page.flags.ignore_permissions = True
		page.save(ignore_permissions=True)
		frappe.db.commit()

	return added
