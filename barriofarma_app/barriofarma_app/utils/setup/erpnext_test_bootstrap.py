# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Infraestructura de test compatible con ERPNext 16 BootStrapTestData.

ERPNext make_shelf() crea Shelf mínimos (solo shelf_name). BarrioFarma exige
warehouse, location_code y shelf_type. Este módulo provisiona estantes válidos
para almacenes _Test* y parchea el bootstrap de ERPNext antes del preload.
"""

from __future__ import annotations

import re
import sys
import types
from pathlib import Path

import frappe

from barriofarma_app.barriofarma_app.test_setup import create_test_shelf
from barriofarma_app.barriofarma_app.utils.shelf_validations import count_active_shelves

_PATCHED = False
_BOOTSTRAPPED = False
_MODULE = "erpnext.tests.utils"


def ensure_test_warehouse_shelves():
	"""Un estante activo por almacén hoja _Test* (Issue #58, sin saltar reglas)."""
	if not frappe.db:
		return

	warehouses = frappe.get_all(
		"Warehouse",
		filters={
			"warehouse_name": ["like", "_Test%"],
			"is_group": 0,
			"disabled": 0,
		},
		fields=["name", "warehouse_name"],
	)

	for row in warehouses:
		if count_active_shelves(row.name) > 0:
			continue

		label = (row.warehouse_name or row.name).replace(" ", "-")[:40]
		create_test_shelf(
			shelf_name=f"Estante test {row.warehouse_name or row.name}",
			warehouse=row.name,
			location_code=f"TEST-{label}",
			shelf_type="Normal",
		)


def _load_erpnext_test_utils_module():
	"""Carga erpnext.tests.utils sin ejecutar BootStrapTestData() a nivel módulo."""
	if _MODULE in sys.modules:
		return sys.modules[_MODULE]

	path = Path(frappe.get_app_path("erpnext", "tests", "utils.py"))
	source = path.read_text()
	# ERPNext ejecuta BootStrapTestData() a nivel módulo; lo diferimos hasta parchear make_shelf.
	source = re.sub(
		r"^BootStrapTestData\(\)\s*$",
		"# BootStrapTestData() deferred by barriofarma_app",
		source,
		count=1,
		flags=re.MULTILINE,
	)

	module = types.ModuleType(_MODULE)
	module.__file__ = str(path)
	exec(compile(source, str(path), "exec"), module.__dict__)
	sys.modules[_MODULE] = module
	return module


def _patched_make_shelf(self):
	ensure_test_warehouse_shelves()


def patch_erpnext_bootstrap_for_barriofarma():
	global _PATCHED, _BOOTSTRAPPED
	if _PATCHED:
		return

	module = _load_erpnext_test_utils_module()
	module.BootStrapTestData.make_shelf = _patched_make_shelf
	_PATCHED = True

	if not _BOOTSTRAPPED and frappe.db and not frappe.db.exists("Company", "_Test Company"):
		module.BootStrapTestData()
		_BOOTSTRAPPED = True
	elif not _BOOTSTRAPPED and frappe.db:
		# Sitio ya tiene datos ERPNext test; solo asegurar estantes faltantes
		ensure_test_warehouse_shelves()
		_BOOTSTRAPPED = True


def patch_compat_preload_doctype_schema_guard():
	"""Evita que compat_preload confunda {doctype}.json (schema) con test records (Frappe v16)."""
	import json
	import os
	import re

	import frappe.deprecation_dumpster as dd
	from frappe.tests.utils import make_test_records

	if getattr(dd.compat_preload_test_records_upfront, "_barriofarma_guard", False):
		return

	_original = dd.compat_preload_test_records_upfront

	def _safe_compat_preload(candidates):
		for module, path, filename in candidates:
			if hasattr(module, "test_dependencies"):
				for doctype in module.test_dependencies:
					make_test_records(doctype, commit=True)
			if hasattr(module, "EXTRA_TEST_RECORD_DEPENDENCIES"):
				for doctype in module.EXTRA_TEST_RECORD_DEPENDENCIES:
					make_test_records(doctype, commit=True)

			if os.path.basename(os.path.dirname(path)) != "doctype":
				continue

			test_record_filename = re.sub("^test_", "", filename).replace(".py", ".json")
			test_record_file_path = os.path.join(path, test_record_filename)
			if not os.path.exists(test_record_file_path):
				continue

			with open(test_record_file_path) as f:
				doc = json.load(f)
			if doc.get("doctype") == "DocType":
				continue

			make_test_records(doc["name"], commit=True)

	_safe_compat_preload._barriofarma_guard = True
	dd.compat_preload_test_records_upfront = _safe_compat_preload


def before_tests():
	"""Hook Frappe: ejecutar antes del preload de test records."""
	patch_compat_preload_doctype_schema_guard()
	patch_erpnext_bootstrap_for_barriofarma()
