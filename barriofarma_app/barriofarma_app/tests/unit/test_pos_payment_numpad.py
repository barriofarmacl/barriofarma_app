# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""POS: no completar pedido si paid < total (partial payment)."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


def _numpad_js() -> Path:
	return Path(__file__).resolve().parents[3] / "public" / "js" / "pos_payment_numpad.js"


def _call(expr: str):
	js = _numpad_js()
	completed = subprocess.run(
		[
			"node",
			"-e",
			f"const m=require({json.dumps(str(js))}); console.log(JSON.stringify({expr}));",
		],
		check=True,
		capture_output=True,
		text=True,
	)
	return json.loads(completed.stdout)


class TestPosCompleteOrderGuard(unittest.TestCase):
	def test_reject_complete_order_when_paid_one_peso(self) -> None:
		decision = _call(
			"m.can_complete_order({item_count:1,paid_amount:1,grand_total:1100,"
			"rounded_total:1100,disable_rounded_total:0,allow_partial_payment:0,"
			"additional_discount_percentage:0})"
		)
		self.assertFalse(decision["ok"])
		self.assertEqual(decision["reason"], "partial")

	def test_allow_complete_when_paid_covers_total(self) -> None:
		decision = _call(
			"m.can_complete_order({item_count:1,paid_amount:1100,grand_total:1100,"
			"rounded_total:1100,disable_rounded_total:0,allow_partial_payment:0,"
			"additional_discount_percentage:0})"
		)
		self.assertTrue(decision["ok"])
