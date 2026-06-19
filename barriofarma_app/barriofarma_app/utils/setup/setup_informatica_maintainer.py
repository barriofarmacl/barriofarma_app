# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# barriofarma-number-cards-platform — prod maintainer roles

import logging

import frappe

logger = logging.getLogger(__name__)

MAINTAINER_EMAIL = "eduardo.araya@barriofarma.cl"
# Administrador plataforma BarrioFarma (PO 2026-06-16): KPIs + workspaces + usuarios.
MAINTAINER_ROLES = (
	"Informática",
	"Dashboard Manager",
	"Workspace Manager",
	"System Manager",
)


def ensure_informatica_maintainer_roles():
	"""Ensure eduardo.araya has platform admin roles (Informática + Desk + User)."""
	if not frappe.db.exists("User", MAINTAINER_EMAIL):
		logger.info("Maintainer user %s not found; skip role sync", MAINTAINER_EMAIL)
		return []

	added = []
	user = frappe.get_doc("User", MAINTAINER_EMAIL)
	existing = {r.role for r in user.roles}

	for role in MAINTAINER_ROLES:
		if not frappe.db.exists("Role", role):
			logger.warning("Role %s missing; skip", role)
			continue
		if role not in existing:
			user.append("roles", {"role": role})
			added.append(role)

	if added:
		user.flags.ignore_permissions = True
		user.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.clear_cache(user=MAINTAINER_EMAIL)
		logger.info("Maintainer roles added for %s: %s", MAINTAINER_EMAIL, added)

	return added
