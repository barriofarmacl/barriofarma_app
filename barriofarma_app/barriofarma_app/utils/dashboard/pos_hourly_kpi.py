# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# barriofarma-number-cards-platform fase 2 — KPI última hora POS

import frappe
from frappe.utils import add_to_date, flt, get_datetime, now_datetime


def resolve_pos_company(filters=None):
	"""Company for POS KPIs: filters, session user default, then global default."""
	company = _company_from_filters(filters)
	if company:
		return company
	company = frappe.defaults.get_user_default("Company")
	if company:
		return company
	return frappe.defaults.get_global_default("company")


def _company_from_filters(filters):
	"""Extract company from Number Card / chart filters (list or dict)."""
	if not filters:
		return None
	if isinstance(filters, dict):
		return filters.get("company")
	if isinstance(filters, list):
		for row in filters:
			if not isinstance(row, (list, tuple)) or len(row) < 4:
				continue
			if row[1] == "company" and row[2] in ("=", "=="):
				return row[3]
	return None


def _normalize_card_filters(filters):
	"""Number Card widget may send null, empty string, or omit filters."""
	if filters in (None, "", "null", "undefined"):
		return None
	if isinstance(filters, str):
		return frappe.parse_json(filters)
	return filters


def last_hour_bounds(now=None):
	"""Rolling 60-minute window in server TZ."""
	now = get_datetime(now or now_datetime())
	return add_to_date(now, minutes=-60), now


def _pos_last_hour_aggregate(company, aggregate="count"):
	start, end = last_hour_bounds()
	if aggregate == "sum":
		field = "COALESCE(SUM(grand_total), 0)"
	else:
		field = "COUNT(*)"
	row = frappe.db.sql(
		f"""
		SELECT {field}
		FROM `tabPOS Invoice`
		WHERE docstatus = 1
		  AND company = %s
		  AND creation >= %s
		  AND creation <= %s
		""",
		(company, start, end),
	)
	return flt(row[0][0]) if row else 0


def _currency_card_value(amount):
	"""Custom Number Card payload so desk applies card.currency (CLP) formatting."""
	return {"value": flt(amount), "fieldtype": "Currency"}


@frappe.whitelist()
def bf_ventas_ultima_hora(filters=None):
	"""Custom Number Card: monto CLP POS en últimos 60 minutos."""
	filters = _normalize_card_filters(filters)
	company = resolve_pos_company(filters)
	if not company:
		return _currency_card_value(0)
	return _currency_card_value(_pos_last_hour_aggregate(company, aggregate="sum"))


@frappe.whitelist()
def bf_tickets_ultima_hora(filters=None):
	"""Custom Number Card: boletas POS submitidas en últimos 60 minutos."""
	filters = _normalize_card_filters(filters)
	company = resolve_pos_company(filters)
	if not company:
		return 0
	return _pos_last_hour_aggregate(company, aggregate="count")


def period_date_bounds(period, now=None):
	"""Map workspace report period filter to [start, end] datetimes."""
	now = get_datetime(now or now_datetime())
	end = now
	period = (period or "Last Week").strip()
	if period == "Today":
		start = get_datetime(now.date())
	elif period == "Last Month":
		start = add_to_date(now, days=-30)
	else:
		start = add_to_date(now, days=-7)
	return start, end


def fetch_hourly_pos_rows(company, start, end):
	"""Aggregate submitted POS invoices by calendar day + hour."""
	if not company:
		return []
	return frappe.db.sql(
		"""
		SELECT
			DATE(creation) AS day,
			HOUR(creation) AS hour_of_day,
			COUNT(*) AS tickets,
			COALESCE(SUM(grand_total), 0) AS amount_clp
		FROM `tabPOS Invoice`
		WHERE docstatus = 1
		  AND company = %s
		  AND creation >= %s
		  AND creation <= %s
		GROUP BY DATE(creation), HOUR(creation)
		ORDER BY day, hour_of_day
		""",
		(company, start, end),
		as_dict=True,
	)


def hourly_row_label(day, hour_of_day):
	return f"{day.strftime('%d-%m-%Y')} {int(hour_of_day):02d}:00"
