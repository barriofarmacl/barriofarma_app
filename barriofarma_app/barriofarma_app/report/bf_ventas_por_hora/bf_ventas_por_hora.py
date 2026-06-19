# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# Change: barriofarma-number-cards-platform fase 2

import frappe
from frappe import _

from barriofarma_app.barriofarma_app.utils.dashboard.pos_hourly_kpi import (
	fetch_hourly_pos_rows,
	hourly_row_label,
	period_date_bounds,
	resolve_pos_company,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	company = resolve_pos_company(filters)
	start, end = period_date_bounds(filters.get("period") or "Last Week")
	rows = fetch_hourly_pos_rows(company, start, end)
	columns = get_columns()
	data = [
		{
			"hour_label": hourly_row_label(row.day, row.hour_of_day),
			"tickets": row.tickets,
			"amount_clp": row.amount_clp,
		}
		for row in rows
	]
	chart = get_chart_data(data)
	return columns, data, None, chart


def get_columns():
	return [
		{
			"fieldname": "hour_label",
			"label": _("Hora"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "amount_clp",
			"label": _("Monto CLP"),
			"fieldtype": "Currency",
			"options": "CLP",
			"width": 140,
		},
		{
			"fieldname": "tickets",
			"label": _("Boletas"),
			"fieldtype": "Int",
			"width": 100,
		},
	]


def get_chart_data(data):
	labels = [row["hour_label"] for row in data]
	amounts = [row["amount_clp"] for row in data]
	tickets = [row["tickets"] for row in data]
	return {
		"type": "line",
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Monto CLP"), "values": amounts},
				{"name": _("Boletas"), "values": tickets},
			],
		},
	}
