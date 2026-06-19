# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# Change: barriofarma-number-cards-platform — widgets POS + embed workspaces

import json
import logging

import frappe

from barriofarma_app.barriofarma_app.utils.dashboard.dashboard_constants import (
	BF_MODULE,
	CH_BF_TICKETS_DIA,
	CH_BF_VENTAS_HORA,
	CUSTOM_CARD_NO_DYNAMIC_FILTERS,
	LEGACY_CH_TICKETS_HORA,
	METHOD_TICKETS_ULTIMA_HORA,
	METHOD_VENTAS_ULTIMA_HORA,
	NC_BF_BOLETA,
	NC_BF_ITEMS,
	NC_BF_OC,
	NC_BF_TICKETS_ULTIMA_HORA,
	NC_BF_VENTAS_ULTIMA_HORA,
	POS_COMPANY_FILTER,
	PO_COMPANY_FILTER,
	REPORT_BF_VENTAS_HORA,
	REPORT_CHART_DYNAMIC_FILTERS,
)
from barriofarma_app.barriofarma_app.utils.dashboard.embed_workspace_content import (
	merge_workspace_widgets,
	normalize_selling_bf_content,
	parse_workspace_content,
	selling_bf_blocks,
)

logger = logging.getLogger(__name__)


def ensure_dashboard_user_company_defaults():
	"""Set Company user default for desk users missing it (POS dashboard dynamic filters)."""
	company = frappe.defaults.get_global_default("company")
	if not company:
		companies = frappe.get_all("Company", limit=1)
		company = companies[0].name if companies else None
	if not company:
		logger.warning("ensure_dashboard_user_company_defaults: no Company in site")
		return

	updated = 0
	for user in frappe.get_all(
		"User", filters={"enabled": 1, "user_type": "System User"}, pluck="name"
	):
		if frappe.defaults.get_user_default("Company", user):
			continue
		frappe.defaults.set_user_default("Company", company, user)
		updated += 1
	if updated:
		logger.info("Set Company default=%s for %s desk users", company, updated)


def ensure_barriofarma_pos_widgets():
	"""Create or update Number Card / Dashboard Chart (is_standard=0). Idempotent."""
	ensure_dashboard_user_company_defaults()
	ensure_bf_boleta_promedio()
	ensure_bf_ventas_ultima_hora()
	ensure_bf_tickets_ultima_hora()
	ensure_bf_tickets_dia()
	ensure_bf_ventas_por_hora_chart()
	_retire_legacy_tickets_hora_chart()
	ensure_bf_oc_pendientes()
	ensure_bf_items_activos()
	frappe.db.commit()


def ensure_bf_boleta_promedio():
	values = {
		"doctype": "Number Card",
		"label": "Boleta Promedio (CLP)",
		"type": "Document Type",
		"document_type": "POS Invoice",
		"function": "Average",
		"aggregate_function_based_on": "grand_total",
		"currency": "CLP",
		"filters_json": json.dumps(
			[
				["POS Invoice", "posting_date", "Timespan", "today"],
				["POS Invoice", "docstatus", "=", 1],
			]
		),
		"dynamic_filters_json": POS_COMPANY_FILTER,
		"is_public": 1,
		"is_standard": 0,
		"module": BF_MODULE,
		"show_full_number": 1,
		"show_percentage_stats": 1,
		"stats_time_interval": "Daily",
	}
	_upsert_doc("Number Card", NC_BF_BOLETA, values)


def ensure_bf_ventas_ultima_hora():
	values = {
		"doctype": "Number Card",
		"label": "Ventas última hora (CLP)",
		"type": "Custom",
		"document_type": "POS Invoice",
		"method": METHOD_VENTAS_ULTIMA_HORA,
		"currency": "CLP",
		"dynamic_filters_json": CUSTOM_CARD_NO_DYNAMIC_FILTERS,
		"is_public": 1,
		"is_standard": 0,
		"module": BF_MODULE,
		"show_full_number": 1,
	}
	_upsert_doc("Number Card", NC_BF_VENTAS_ULTIMA_HORA, values)


def ensure_bf_tickets_ultima_hora():
	values = {
		"doctype": "Number Card",
		"label": "Boletas última hora",
		"type": "Custom",
		"document_type": "POS Invoice",
		"method": METHOD_TICKETS_ULTIMA_HORA,
		"dynamic_filters_json": CUSTOM_CARD_NO_DYNAMIC_FILTERS,
		"is_public": 1,
		"is_standard": 0,
		"module": BF_MODULE,
		"show_full_number": 1,
	}
	_upsert_doc("Number Card", NC_BF_TICKETS_ULTIMA_HORA, values)


def ensure_bf_tickets_dia():
	values = {
		"doctype": "Dashboard Chart",
		"chart_name": CH_BF_TICKETS_DIA,
		"chart_type": "Count",
		"document_type": "POS Invoice",
		"based_on": "posting_date",
		"timeseries": 1,
		"time_interval": "Daily",
		"timespan": "Last Month",
		"type": "Bar",
		"filters_json": json.dumps([["POS Invoice", "docstatus", "=", 1]]),
		"dynamic_filters_json": POS_COMPANY_FILTER,
		"is_public": 1,
		"is_standard": 0,
		"module": BF_MODULE,
	}
	_upsert_doc("Dashboard Chart", CH_BF_TICKETS_DIA, values)


def ensure_bf_ventas_por_hora_chart():
	if not frappe.db.exists("Report", REPORT_BF_VENTAS_HORA):
		logger.warning("Report %s missing; run bench migrate", REPORT_BF_VENTAS_HORA)
	values = {
		"doctype": "Dashboard Chart",
		"chart_name": CH_BF_VENTAS_HORA,
		"chart_type": "Report",
		"report_name": REPORT_BF_VENTAS_HORA,
		"use_report_chart": 1,
		"type": "Line",
		"filters_json": json.dumps({"period": "Last Week"}),
		"dynamic_filters_json": REPORT_CHART_DYNAMIC_FILTERS,
		"is_public": 1,
		"is_standard": 0,
		"module": BF_MODULE,
	}
	_upsert_doc("Dashboard Chart", CH_BF_VENTAS_HORA, values)


def _retire_legacy_tickets_hora_chart():
	if not frappe.db.exists("Dashboard Chart", LEGACY_CH_TICKETS_HORA):
		return
	if LEGACY_CH_TICKETS_HORA == CH_BF_VENTAS_HORA:
		return
	try:
		frappe.delete_doc("Dashboard Chart", LEGACY_CH_TICKETS_HORA, ignore_permissions=True, force=True)
		logger.info("Removed legacy Dashboard Chart %s", LEGACY_CH_TICKETS_HORA)
	except Exception as exc:
		logger.warning("Could not remove legacy chart %s: %s", LEGACY_CH_TICKETS_HORA, exc)


def ensure_bf_oc_pendientes():
	values = {
		"doctype": "Number Card",
		"label": "OC pendientes recepción",
		"type": "Document Type",
		"document_type": "Purchase Order",
		"function": "Count",
		"filters_json": json.dumps(
			[
				["Purchase Order", "docstatus", "=", 1],
				["Purchase Order", "status", "in", ["To Receive and Bill", "To Receive"]],
			]
		),
		"dynamic_filters_json": PO_COMPANY_FILTER,
		"is_public": 1,
		"is_standard": 0,
		"module": BF_MODULE,
	}
	_upsert_doc("Number Card", NC_BF_OC, values)


def ensure_bf_items_activos():
	values = {
		"doctype": "Number Card",
		"label": "SKUs activos",
		"type": "Document Type",
		"document_type": "Item",
		"function": "Count",
		"filters_json": json.dumps([["Item", "disabled", "=", 0]]),
		"dynamic_filters_json": "[]",
		"is_public": 1,
		"is_standard": 0,
		"module": BF_MODULE,
	}
	_upsert_doc("Number Card", NC_BF_ITEMS, values)


def _reconcile_number_card_name(target_name, label):
	"""Rename label-autonamed legacy cards to stable BF names."""
	if frappe.db.exists("Number Card", target_name):
		return
	legacy = frappe.db.get_value(
		"Number Card",
		{"label": label, "module": BF_MODULE},
		"name",
	)
	if legacy and legacy != target_name:
		frappe.rename_doc("Number Card", legacy, target_name, force=True, merge=False)


def _upsert_doc(doctype, name, values):
	if doctype == "Number Card":
		_reconcile_number_card_name(name, values.get("label"))

	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		for key, val in values.items():
			if key != "doctype":
				setattr(doc, key, val)
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
		return

	doc = frappe.get_doc(values)
	if doctype == "Number Card":
		doc.name = name
	doc.flags.ignore_permissions = True
	if doctype == "Number Card":
		frappe.flags.in_import = True
	try:
		doc.insert(ignore_permissions=True)
	finally:
		if doctype == "Number Card":
			frappe.flags.in_import = False


def embed_barriofarma_workspace_widgets():
	"""Patch Workspace documents in BD (Selling, Buying, Stock). Idempotent."""
	_embed_selling()
	_embed_buying()
	_embed_stock()
	frappe.db.commit()


def _embed_selling():
	ws = frappe.get_doc("Workspace", "Selling")
	content = normalize_selling_bf_content(parse_workspace_content(ws.content))
	blocks = selling_bf_blocks()
	new_content = merge_workspace_widgets(content, blocks)
	if new_content != parse_workspace_content(ws.content):
		ws.content = json.dumps(new_content)
	_remove_child_row(ws, "charts", "chart_name", LEGACY_CH_TICKETS_HORA)
	for chart_name in (CH_BF_VENTAS_HORA, CH_BF_TICKETS_DIA):
		_append_child_row(ws, "charts", "chart_name", chart_name)
	for card_name in (NC_BF_VENTAS_ULTIMA_HORA, NC_BF_TICKETS_ULTIMA_HORA, NC_BF_BOLETA):
		_append_child_row(ws, "number_cards", "number_card_name", card_name)
	ws.flags.ignore_permissions = True
	ws.save(ignore_permissions=True)


def _embed_buying():
	ws = frappe.get_doc("Workspace", "Buying")
	content = parse_workspace_content(ws.content)
	header = selling_bf_blocks()[0]
	header["data"]["text"] = '<span class="h4"><b>Compras BarrioFarma</b></span>'
	blocks = [
		header,
		{
			"id": "bfbuy1",
			"type": "number_card",
			"data": {"number_card_name": NC_BF_OC, "col": 4},
		},
	]
	new_content = merge_workspace_widgets(content, blocks)
	if new_content != content:
		ws.content = json.dumps(new_content)
	_append_child_row(ws, "number_cards", "number_card_name", NC_BF_OC)
	ws.flags.ignore_permissions = True
	ws.save(ignore_permissions=True)


def _embed_stock():
	ws = frappe.get_doc("Workspace", "Stock")
	content = parse_workspace_content(ws.content)
	header = selling_bf_blocks()[0]
	header["data"]["text"] = '<span class="h4"><b>Stock BarrioFarma</b></span>'
	blocks = [
		header,
		{
			"id": "bfstk1",
			"type": "number_card",
			"data": {"number_card_name": NC_BF_ITEMS, "col": 4},
		},
	]
	new_content = merge_workspace_widgets(content, blocks)
	if new_content != content:
		ws.content = json.dumps(new_content)
	_append_child_row(ws, "number_cards", "number_card_name", NC_BF_ITEMS)
	ws.flags.ignore_permissions = True
	ws.save(ignore_permissions=True)


def _append_child_row(doc, tablefield, name_field, name):
	existing = {getattr(row, name_field) for row in doc.get(tablefield) or []}
	if name not in existing:
		doc.append(tablefield, {name_field: name, "label": name})


def _remove_child_row(doc, tablefield, name_field, name):
	rows = doc.get(tablefield) or []
	doc.set(tablefield, [row for row in rows if getattr(row, name_field) != name])


def setup_barriofarma_dashboard():
	"""Entry point for after_migrate."""
	try:
		ensure_barriofarma_pos_widgets()
		embed_barriofarma_workspace_widgets()
		frappe.clear_cache()
		logger.info("BarrioFarma dashboard widgets: ensure + embed OK")
	except Exception as exc:
		logger.error("BarrioFarma dashboard widgets failed: %s", exc)
		raise
