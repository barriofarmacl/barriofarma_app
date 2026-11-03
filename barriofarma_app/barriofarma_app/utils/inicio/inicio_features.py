# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Flags de modulos expuestos por la SPA inicio (turnos vs catalogo terreno)."""

from __future__ import annotations

import frappe
from frappe.utils import cint


def catalogo_terreno_enabled() -> bool:
	"""
	Catalogo terreno (vendedor en campo) puede apagarse por sitio.

	UAT farmacia / cierre freeze #80: en ``site_config.json`` del sitio UAT:

		"inicio_catalogo_terreno_enabled": 0

	Turnos (/turno, /pantalla) no usan esta flag.
	"""
	raw = frappe.conf.get("inicio_catalogo_terreno_enabled")
	if raw is None:
		return True
	return cint(raw) != 0


def inject_inicio_boot_session(bootinfo) -> None:
	bootinfo.inicio_catalogo_terreno_enabled = catalogo_terreno_enabled()
