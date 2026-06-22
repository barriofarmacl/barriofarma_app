# -*- coding: utf-8 -*-
"""Frappe v16: get_desktop_icons no llama DesktopIcon.is_permitted; filtrar por política BF."""

import frappe
from frappe.desk.doctype.desktop_icon.desktop_icon import (
	clear_desktop_icons_cache,
	get_desktop_icons as frappe_get_desktop_icons,
)

from barriofarma_app.barriofarma_app.utils.permissions.desktop_icon_policy import (
	get_hidden_desktop_icons,
)


def _filter_desktop_icons(icons, hidden_labels):
	if not hidden_labels:
		return icons

	filtered = [icon for icon in icons if icon.get("label") not in hidden_labels]
	allowed_parents = {icon.get("label") for icon in filtered if not icon.get("parent_icon")}
	return [
		icon
		for icon in filtered
		if not icon.get("parent_icon") or icon.get("parent_icon") in allowed_parents
	]


def get_desktop_icons(user=None, bootinfo=None):
	user = user or frappe.session.user
	icons = frappe_get_desktop_icons(user=user, bootinfo=bootinfo)
	hidden = get_hidden_desktop_icons(user)
	return _filter_desktop_icons(icons, hidden)


def filter_boot_desktop_icons(bootinfo):
	"""boot_session: aplica política BF a iconos ya cargados en boot."""
	user = frappe.session.user
	hidden = get_hidden_desktop_icons(user)
	if hidden and bootinfo.get("desktop_icons"):
		bootinfo.desktop_icons = _filter_desktop_icons(bootinfo.desktop_icons, hidden)


def register_desktop_icon_v16_patch():
	"""Parchea get_desktop_icons al importar hooks (persistente en workers)."""
	import frappe.desk.doctype.desktop_icon.desktop_icon as desktop_icon_module

	if desktop_icon_module.get_desktop_icons is get_desktop_icons:
		return

	desktop_icon_module.get_desktop_icons = get_desktop_icons


def apply_desktop_icon_v16_patch():
	"""Idempotente: usado en after_migrate y bench execute."""
	register_desktop_icon_v16_patch()
	frappe.clear_cache()


def refresh_desktop_icons_for_users(emails):
	for email in emails:
		clear_desktop_icons_cache(user=email)
		frappe.cache.hdel("bootinfo", email)


def test_desktop_filter(email="natalia.araya@barriofarma.cl"):
	"""Smoke: iconos Desk tras política BF (bench execute)."""
	register_desktop_icon_v16_patch()
	clear_desktop_icons_cache(user=email)
	frappe.set_user(email)
	hidden = get_hidden_desktop_icons(email)
	from frappe.boot import get_bootinfo

	boot = get_bootinfo()
	icons = get_desktop_icons(user=email, bootinfo=boot)
	labels = sorted(i.get("label") for i in icons)
	print(f"{email} hidden={len(hidden)} desktop={labels}")
	return labels
