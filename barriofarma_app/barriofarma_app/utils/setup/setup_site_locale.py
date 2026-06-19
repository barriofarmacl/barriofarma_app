# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# Locale del sitio resuelto por configuracion (no hardcode operativo).
# Evita posting_date / POS opening desfasados (Frappe default Asia/Kolkata).

import os

import frappe

# Fallback de seguridad: solo se usa si ningun nivel de configuracion lo define.
# Operacion BarrioFarma es Chile; cada entorno puede sobreescribir via site_config.json
# (clave bf_time_zone, ...) o variable de entorno (BF_TIME_ZONE, ...).
DEFAULT_LOCALE = {
	"time_zone": "America/Santiago",
	"country": "Chile",
	"language": "es",
	"currency": "CLP",
}

# Mapeo campo System Settings -> clave de configuracion / variable de entorno.
_CONFIG_KEYS = {
	"time_zone": "bf_time_zone",
	"country": "bf_country",
	"language": "bf_language",
	"currency": "bf_currency",
}

# Compatibilidad: modulos que importan la constante siguen funcionando (= fallback).
BARRIOFARMA_TIME_ZONE = DEFAULT_LOCALE["time_zone"]
BARRIOFARMA_COUNTRY = DEFAULT_LOCALE["country"]
BARRIOFARMA_LANGUAGE = DEFAULT_LOCALE["language"]
BARRIOFARMA_CURRENCY = DEFAULT_LOCALE["currency"]


def _conf_get(key: str):
	"""Lee frappe.conf de forma segura (puede no estar enlazado en before_install/tests)."""
	try:
		return frappe.conf.get(key)
	except Exception:
		return None


def _resolve(field: str) -> str:
	"""Resolucion por entorno: site_config.json / common_site_config.json -> env var -> fallback."""
	key = _CONFIG_KEYS[field]
	# frappe.conf fusiona site_config.json sobre common_site_config.json.
	value = _conf_get(key) or os.environ.get(key.upper())
	return value or DEFAULT_LOCALE[field]


def get_barriofarma_locale() -> dict:
	"""Locale efectivo del entorno actual (resuelto, sin valor en duro operativo)."""
	return {field: _resolve(field) for field in DEFAULT_LOCALE}


def get_default_time_zone() -> str:
	"""Zona horaria por defecto para usuarios/validaciones (resuelta por entorno)."""
	return _resolve("time_zone")


def ensure_barriofarma_site_locale():
	"""Idempotente: alinea System Settings al locale resuelto del entorno."""
	from barriofarma_app.barriofarma_app.validations.user_timezone import (
		ensure_all_users_americas_timezone,
	)

	locale = get_barriofarma_locale()
	changed = []

	for field, expected in locale.items():
		current = frappe.db.get_single_value("System Settings", field)
		if current != expected:
			frappe.db.set_single_value("System Settings", field, expected)
			changed.append(f"{field}: {current} -> {expected}")

	if changed:
		frappe.db.commit()
		frappe.clear_cache()
		frappe.logger().info("BarrioFarma site locale: %s", "; ".join(changed))

	user_fixes = ensure_all_users_americas_timezone()
	if user_fixes:
		frappe.logger().info("BarrioFarma user timezones: %s", "; ".join(user_fixes))
		changed.extend(user_fixes)

	return changed
