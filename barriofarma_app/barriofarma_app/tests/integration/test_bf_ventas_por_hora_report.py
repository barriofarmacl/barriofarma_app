# -*- coding: utf-8 -*-
# Issue: barriofarma-number-cards-platform fase 2

import frappe
from frappe.tests.utils import FrappeTestCase


class TestBfVentasPorHoraReport(FrappeTestCase):
	def test_report_runs_via_module_not_empty_script(self):
		report = frappe.get_doc("Report", "BF Ventas por Hora")
		self.assertEqual(report.is_standard, "Yes")

		from frappe.desk.query_report import run

		result = run(
			"BF Ventas por Hora",
			filters={"period": "Last Week", "company": "Barriofarma"},
			ignore_prepared_report=True,
		)
		self.assertIn("columns", result)
		self.assertIn("result", result)
		self.assertIn("chart", result)
		fieldnames = {col["fieldname"] for col in result["columns"]}
		self.assertIn("hour_label", fieldnames)
		self.assertIn("amount_clp", fieldnames)
		self.assertIn("tickets", fieldnames)
