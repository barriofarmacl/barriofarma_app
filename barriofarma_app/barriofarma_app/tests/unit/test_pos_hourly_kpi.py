# -*- coding: utf-8 -*-
# Issue: barriofarma-number-cards-platform fase 2

import unittest
from datetime import datetime

from frappe.utils import add_to_date, get_datetime

from barriofarma_app.barriofarma_app.utils.dashboard.pos_hourly_kpi import (
	_company_from_filters,
	_normalize_card_filters,
	hourly_row_label,
	last_hour_bounds,
	period_date_bounds,
	resolve_pos_company,
)


class TestPosHourlyKpi(unittest.TestCase):
	def test_last_hour_bounds_rolling_sixty_minutes(self):
		now = get_datetime("2026-06-09 15:30:00")
		start, end = last_hour_bounds(now)
		self.assertEqual(end, now)
		self.assertEqual(start, add_to_date(now, minutes=-60))

	def test_period_date_bounds_today(self):
		now = get_datetime("2026-06-09 15:30:00")
		start, end = period_date_bounds("Today", now=now)
		self.assertEqual(start, get_datetime(datetime(2026, 6, 9).date()))
		self.assertEqual(end, now)

	def test_period_date_bounds_last_week_default(self):
		now = get_datetime("2026-06-09 15:30:00")
		start, end = period_date_bounds("Last Week", now=now)
		self.assertEqual(end, now)
		self.assertEqual(start, add_to_date(now, days=-7))

	def test_period_date_bounds_last_month(self):
		now = get_datetime("2026-06-09 15:30:00")
		start, end = period_date_bounds("Last Month", now=now)
		self.assertEqual(end, now)
		self.assertEqual(start, add_to_date(now, days=-30))

	def test_hourly_row_label_format(self):
		day = datetime(2026, 6, 9).date()
		self.assertEqual(hourly_row_label(day, 9), "09-06-2026 09:00")

	def test_company_from_filters_list_format(self):
		filters = [["POS Invoice", "company", "=", "Barriofarma"]]
		self.assertEqual(_company_from_filters(filters), "Barriofarma")

	def test_company_from_filters_dict_format(self):
		self.assertEqual(_company_from_filters({"company": "Barriofarma"}), "Barriofarma")

	def test_company_from_filters_empty_returns_none(self):
		self.assertIsNone(_company_from_filters(None))
		self.assertIsNone(_company_from_filters([]))

	def test_normalize_card_filters_empty_and_null(self):
		self.assertIsNone(_normalize_card_filters(None))
		self.assertIsNone(_normalize_card_filters(""))
		self.assertIsNone(_normalize_card_filters("null"))

	def test_resolve_pos_company_global_fallback(self):
		with unittest.mock.patch(
			"barriofarma_app.barriofarma_app.utils.dashboard.pos_hourly_kpi.frappe.defaults.get_user_default",
			return_value=None,
		), unittest.mock.patch(
			"barriofarma_app.barriofarma_app.utils.dashboard.pos_hourly_kpi.frappe.defaults.get_global_default",
			return_value="Barriofarma",
		):
			self.assertEqual(resolve_pos_company(None), "Barriofarma")

	def test_bf_ventas_ultima_hora_returns_currency_card_payload(self):
		from barriofarma_app.barriofarma_app.utils.dashboard.pos_hourly_kpi import (
			_currency_card_value,
			bf_ventas_ultima_hora,
		)

		self.assertEqual(_currency_card_value(43859.99), {"value": 43859.99, "fieldtype": "Currency"})

		with unittest.mock.patch(
			"barriofarma_app.barriofarma_app.utils.dashboard.pos_hourly_kpi.resolve_pos_company",
			return_value=None,
		):
			self.assertEqual(
				bf_ventas_ultima_hora(),
				{"value": 0.0, "fieldtype": "Currency"},
			)
