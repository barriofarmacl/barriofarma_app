# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Stock Availability Report must stay a standard Script Report.

Desk run fails with RestrictedPython TypeError when the fixture marks the
report is_standard=No and report_script is empty: execute_script compiles None.
"""

import json
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[3]
REPORT_NAME = "Stock Availability Report"


def _report_entry(path):
	payload = json.loads(path.read_text())
	if isinstance(payload, dict):
		return payload
	for row in payload:
		if row.get("name") == REPORT_NAME:
			return row
	raise AssertionError(f"{REPORT_NAME} missing from {path}")


class TestStockAvailabilityReportStandard(unittest.TestCase):
	def test_fixture_keeps_standard_module_report(self):
		fixture = _report_entry(APP_ROOT / "fixtures" / "report.json")
		module = _report_entry(
			APP_ROOT
			/ "barriofarma_app"
			/ "report"
			/ "stock_availability_report"
			/ "stock_availability_report.json"
		)

		self.assertEqual(fixture["is_standard"], "Yes")
		self.assertEqual(fixture["report_type"], "Script Report")
		self.assertEqual(module["is_standard"], "Yes")
		self.assertFalse(fixture.get("report_script"))
