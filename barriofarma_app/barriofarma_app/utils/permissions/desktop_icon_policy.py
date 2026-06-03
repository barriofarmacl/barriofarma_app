# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Política de iconos del escritorio (Desk) por perfil BarrioFarma.

Frappe v16 filtra workspaces por block_modules del User. Algunos iconos ERPNext
mapean a módulos distintos del área funcional (Organization -> Setup,
Subcontracting -> Buying). Este módulo centraliza excepciones por perfil.
"""

import frappe

from barriofarma_app.barriofarma_app.utils.permissions.setup_user_profiles import (
	USER_PROFILES,
)

ROLE_TO_PROFILE = {
	"Farmacéutico": "Perfil Farmacéutico",
	"Auxiliar": "Perfil Auxiliar",
	"Bodeguero": "Perfil Bodeguero",
	"Administrativo": "Perfil Administrativo",
	"Contabilidad": "Perfil Contabilidad",
}

# Carpeta Contabilidad y workspaces hijos (module Accounts)
ACCOUNTING_DESKTOP_ICONS = {
	"Accounting",
	"Payments",
	"Invoicing",
	"Accounts Setup",
	"Taxes",
	"Budget",
	"Subscription",
	"Banking",
	"Financial Reports",
	"Share Management",
}

# Iconos Setup que no queremos al desbloquear Setup solo por Organization
SETUP_DESKTOP_ICONS_TO_HIDE = {
	"Home",
	"ERPNext Settings",
}

# Workspaces fuera del flujo DDD actual
OPTIONAL_DESKTOP_ICONS_TO_HIDE = {
	"Subcontracting",
}

# Iconos técnicos / módulos no operativos en mostrador (perfiles farmacia).
# No incluir "ERPNext": Buying/Selling/Stock son hijos de ese folder en v16.
OPERATIONAL_DESKTOP_ICONS_TO_HIDE = {
	"CRM",
	"Framework",
	"Automation",
	"Email",
}

FOLDER_LABEL_TO_MODULE = {
	"Accounting": "Accounts",
}


def get_profile_name_for_user(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return None
	for role, profile_name in ROLE_TO_PROFILE.items():
		if role in frappe.get_roles(user):
			return profile_name
	return None


def get_desktop_icon_policy(user=None):
	profile_name = get_profile_name_for_user(user)
	if not profile_name:
		return {}
	return USER_PROFILES.get(profile_name, {})


def get_hidden_desktop_icons(user=None):
	user = user or frappe.session.user
	policy = get_desktop_icon_policy(user)
	profile_name = get_profile_name_for_user(user)

	hidden = set(policy.get("hidden_desktop_icons") or [])
	hidden |= SETUP_DESKTOP_ICONS_TO_HIDE
	hidden |= OPTIONAL_DESKTOP_ICONS_TO_HIDE

	if profile_name:
		# Perfiles BarrioFarma mapeados (farmacia, bodega, admin, contabilidad)
		hidden |= OPERATIONAL_DESKTOP_ICONS_TO_HIDE
		if not policy.get("visible_accounts_desktop", False):
			hidden |= ACCOUNTING_DESKTOP_ICONS
	else:
		# System Manager, Administrator, etc.: no aplicar política farmacia.
		# Solo ocultar Contabilidad si el usuario tiene Accounts en block_modules.
		blocked = frappe.get_cached_doc("User", user).get_blocked_modules()
		if "Accounts" in blocked:
			hidden |= ACCOUNTING_DESKTOP_ICONS

	return hidden


def get_extra_desktop_icons(user=None):
	policy = get_desktop_icon_policy(user)
	return set(policy.get("extra_desktop_icons") or [])
