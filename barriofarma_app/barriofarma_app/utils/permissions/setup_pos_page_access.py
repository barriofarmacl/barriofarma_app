# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Acceso a la página Desk ``point-of-sale``.

ERPNext restringe la Page a roles estándar (Sales User, Accounts User, …).
Los perfiles operativos usan roles custom (Farmacéutico, Auxiliar) con DocPerm
en POS Invoice; sin este ajuste Frappe devuelve «Not permitted» al abrir /desk/point-of-sale.

La Page trae ``restrict_to_domain = Retail``. En sitios sin dominio Retail activo,
Frappe excluye el ítem del Workspace Sidebar (Ventas) aunque el usuario tenga rol en la Page.
Se limpia ese dominio para que el enlace «POS» aparezca en el sidebar operativo.
"""

import frappe

POINT_OF_SALE_PAGE = "point-of-sale"

BARRIOFARMA_POS_PAGE_ROLES = ("Farmacéutico", "Auxiliar")


def setup_point_of_sale_page_roles():
	"""Idempotente: roles BarrioFarma en Page point-of-sale y dominio para sidebar."""
	if not frappe.db.exists("Page", POINT_OF_SALE_PAGE):
		frappe.logger().warning("Page %s no existe; se omite setup POS", POINT_OF_SALE_PAGE)
		return []

	added_roles = []
	page = frappe.get_doc("Page", POINT_OF_SALE_PAGE)
	existing = {row.role for row in page.roles}
	changed = False

	for role in BARRIOFARMA_POS_PAGE_ROLES:
		if role not in existing:
			page.append("roles", {"role": role})
			added_roles.append(role)
			changed = True

	if page.restrict_to_domain:
		page.restrict_to_domain = ""
		changed = True

	if changed:
		page.flags.ignore_permissions = True
		page.save(ignore_permissions=True)
		frappe.db.commit()
		_rebuild_domain_restricted_page_cache()

	return added_roles


def _rebuild_domain_restricted_page_cache():
	from frappe.cache_manager import build_domain_restricted_page_cache

	build_domain_restricted_page_cache()
