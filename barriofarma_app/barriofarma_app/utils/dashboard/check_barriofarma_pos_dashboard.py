# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# Smoke: barriofarma-number-cards-platform

import frappe

from barriofarma_app.barriofarma_app.utils.dashboard.dashboard_constants import (
	CH_BF_TICKETS_DIA,
	CH_BF_VENTAS_HORA,
	LEGACY_CH_TICKETS_HORA,
	NC_BF_BOLETA,
	NC_BF_TICKETS_ULTIMA_HORA,
	NC_BF_VENTAS_ULTIMA_HORA,
	REPORT_BF_VENTAS_HORA,
)
from barriofarma_app.barriofarma_app.utils.dashboard.embed_workspace_content import (
	content_references_widget,
	parse_workspace_content,
)

BF_WIDGETS = (
	("number_card", NC_BF_VENTAS_ULTIMA_HORA),
	("number_card", NC_BF_TICKETS_ULTIMA_HORA),
	("number_card", NC_BF_BOLETA),
	("chart", CH_BF_VENTAS_HORA),
	("chart", CH_BF_TICKETS_DIA),
)

MAINTAINER_EMAIL = "eduardo.araya@barriofarma.cl"


def check_barriofarma_pos_dashboard():
	"""Verify BF POS widgets exist and maintainer can write Number Card."""
	for doctype, name in (
		("Number Card", NC_BF_VENTAS_ULTIMA_HORA),
		("Number Card", NC_BF_TICKETS_ULTIMA_HORA),
		("Number Card", NC_BF_BOLETA),
		("Dashboard Chart", CH_BF_VENTAS_HORA),
		("Dashboard Chart", CH_BF_TICKETS_DIA),
		("Report", REPORT_BF_VENTAS_HORA),
	):
		if not frappe.db.exists(doctype, name):
			print(f"MISSING {doctype}: {name}")
			continue
		if doctype == "Report":
			print(f"OK Report {name}")
			continue
		row = frappe.db.get_value(
			doctype, name, ["is_standard", "module"], as_dict=True
		)
		print(f"OK {doctype} {name} is_standard={row.is_standard} module={row.module}")

	if frappe.db.exists("Dashboard Chart", LEGACY_CH_TICKETS_HORA):
		print(f"WARN legacy chart still present: {LEGACY_CH_TICKETS_HORA}")

	ws = frappe.get_doc("Workspace", "Selling")
	content = parse_workspace_content(ws.content)
	for block_type, name in BF_WIDGETS:
		ok = content_references_widget(content, block_type, name)
		print(f"Selling embed {name}: {ok}")

	if frappe.db.exists("User", MAINTAINER_EMAIL):
		frappe.set_user(MAINTAINER_EMAIL)
		write_ok = frappe.has_permission("Number Card", "write")
		print(f"{MAINTAINER_EMAIL} Number Card write={write_ok}")
		frappe.set_user("Administrator")
	else:
		print(f"User {MAINTAINER_EMAIL} not found — skip perm check")
