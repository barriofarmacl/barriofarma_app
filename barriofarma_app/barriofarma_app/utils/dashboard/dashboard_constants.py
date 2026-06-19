# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# barriofarma-number-cards-platform — widget names (single source of truth)

BF_MODULE = "Barriofarma App"

NC_BF_BOLETA = "BF Boleta Promedio"
NC_BF_VENTAS_ULTIMA_HORA = "BF Ventas Última Hora"
NC_BF_TICKETS_ULTIMA_HORA = "BF Tickets Última Hora"
NC_BF_OC = "BF OC Pendientes Recepción"
NC_BF_ITEMS = "BF Items Activos"

CH_BF_TICKETS_DIA = "BF Tickets Día"
CH_BF_VENTAS_HORA = "BF Ventas por Hora"
LEGACY_CH_TICKETS_HORA = "BF Tickets Hora"

REPORT_BF_VENTAS_HORA = "BF Ventas por Hora"

POS_COMPANY_FILTER = '[["POS Invoice","company","=", "frappe.defaults.get_user_default(\\"Company\\")"]]'
PO_COMPANY_FILTER = '[["Purchase Order","company","=", "frappe.defaults.get_user_default(\\"Company\\")"]]'

# Custom Number Cards resolve company server-side; avoid client eval on dynamic filters.
CUSTOM_CARD_NO_DYNAMIC_FILTERS = "[]"

# Report Dashboard Chart: never store literal company values (Frappe eval() on dict values).
REPORT_CHART_DYNAMIC_FILTERS = "{}"

METHOD_VENTAS_ULTIMA_HORA = (
	"barriofarma_app.barriofarma_app.utils.dashboard.pos_hourly_kpi.bf_ventas_ultima_hora"
)
METHOD_TICKETS_ULTIMA_HORA = (
	"barriofarma_app.barriofarma_app.utils.dashboard.pos_hourly_kpi.bf_tickets_ultima_hora"
)
