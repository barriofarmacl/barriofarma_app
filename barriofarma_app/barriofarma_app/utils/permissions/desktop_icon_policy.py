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
	policy = get_desktop_icon_policy(user)
	hidden = set(policy.get("hidden_desktop_icons") or [])
	hidden |= set(ACCOUNTING_DESKTOP_ICONS)
	hidden |= set(SETUP_DESKTOP_ICONS_TO_HIDE)
	hidden |= set(OPTIONAL_DESKTOP_ICONS_TO_HIDE)
	if not policy.get("visible_accounts_desktop", False):
		pass  # ACCOUNTING_DESKTOP_ICONS ya incluidos salvo perfil contable
	if policy.get("visible_accounts_desktop"):
		hidden -= ACCOUNTING_DESKTOP_ICONS
	return hidden


def get_extra_desktop_icons(user=None):
	policy = get_desktop_icon_policy(user)
	return set(policy.get("extra_desktop_icons") or [])
