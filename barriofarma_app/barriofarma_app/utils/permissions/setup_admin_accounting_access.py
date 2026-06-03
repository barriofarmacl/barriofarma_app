# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Perfiles administrativos: permisos contables vía roles estándar ERPNext.

Los roles custom ``Administrativo`` y ``Contabilidad`` no sobrescriben DocPerm
(ver ``ERPNEXT_STANDARD_PERMISSION_ROLES`` en setup_permissions.py).

Este módulo reaplica perfiles UAT y valida acceso a pagos y plan de cuentas.
"""

import frappe

from barriofarma_app.barriofarma_app.utils.permissions.setup_user_profiles import (
	USER_PROFILES,
	setup_user_from_profile,
)

DEFAULT_ADMIN_UAT_EMAILS = (
	"karla.carmona@barriofarma.cl",
	"jimena.araya@barriofarma.cl",
)


def apply_admin_profiles(emails=None):
	"""Reaplica Perfil Administrativo a usuarios UAT administrativos."""
	emails = emails or DEFAULT_ADMIN_UAT_EMAILS
	results = []
	for email in emails:
		if not frappe.db.exists("User", email):
			results.append({"email": email, "skipped": True})
			continue
		full_name = frappe.db.get_value("User", email, "full_name")
		out = setup_user_from_profile(
			email=email,
			profile_name="Perfil Administrativo",
			full_name=full_name,
			enabled=True,
		)
		results.append({"email": email, "success": out.get("success", False)})
	frappe.db.commit()
	return results


def get_admin_profile_summary(email):
	"""Resumen de roles y permisos contables efectivos para un usuario admin."""
	if not frappe.db.exists("User", email):
		return None

	frappe.set_user(email)
	frappe.get_user().build_permissions()
	roles = frappe.get_roles(email)
	blocked = frappe.get_cached_doc("User", email).get_blocked_modules()

	checks = {}
	for dt, perms in (
		("Payment Entry", ("read", "write", "create", "submit")),
		("Journal Entry", ("read", "write", "create", "submit")),
		("Account", ("read", "write", "create")),
		("Purchase Invoice", ("read", "write", "submit")),
		("Purchase Order", ("read", "write", "submit")),
		("GL Entry", ("read",)),
	):
		checks[dt] = {p: frappe.has_permission(dt, p) for p in perms}

	return {
		"email": email,
		"roles": roles,
		"accounts_module_blocked": "Accounts" in blocked,
		"has_accounts_manager": "Accounts Manager" in roles,
		"permissions": checks,
		"profile": USER_PROFILES.get("Perfil Administrativo", {}),
	}
