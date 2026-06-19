# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# Política: usuarios BarrioFarma solo zonas America/* (operación Chile/LATAM).

import frappe
from frappe import _

from barriofarma_app.barriofarma_app.utils.setup.setup_site_locale import get_default_time_zone

AMERICA_TIMEZONE_PREFIX = "America/"
SKIP_USER_NAMES = frozenset({"Guest"})


def is_americas_timezone(time_zone: str | None) -> bool:
	if not time_zone:
		return False
	return str(time_zone).startswith(AMERICA_TIMEZONE_PREFIX)


def apply_default_user_timezone(doc, method=None):
	"""before_insert: default America/Santiago si no viene zona horaria."""
	if doc.name in SKIP_USER_NAMES:
		return
	if not doc.time_zone:
		doc.time_zone = get_default_time_zone()


def validate_user_americas_timezone(doc, method=None):
	"""validate: rechazar zonas fuera de America/*."""
	if doc.name in SKIP_USER_NAMES:
		return

	if not doc.time_zone:
		doc.time_zone = get_default_time_zone()
		return

	if is_americas_timezone(doc.time_zone):
		return

	frappe.throw(
		_(
			"La zona horaria {0} no está permitida. Use una zona bajo America/ (por ejemplo America/Santiago)."
		).format(frappe.bold(doc.time_zone)),
		title=_("Zona horaria no permitida"),
	)


def ensure_all_users_americas_timezone() -> list[str]:
	"""Idempotente: corrige usuarios con Asia/Kolkata u otras zonas no-America."""
	default_tz = get_default_time_zone()
	fixed = []
	for row in frappe.get_all(
		"User",
		filters={"name": ["not in", list(SKIP_USER_NAMES)]},
		fields=["name", "time_zone"],
	):
		current = row.time_zone or ""
		if is_americas_timezone(current):
			continue
		frappe.db.set_value("User", row.name, "time_zone", default_tz, update_modified=False)
		fixed.append(f"{row.name}: {current or '(vacío)'} -> {default_tz}")

	if fixed:
		frappe.db.commit()
		frappe.clear_cache()

	return fixed
