# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Aviso de conciliación cuando el libro de inventario ya está en negativo."""

import unittest
from unittest.mock import MagicMock, patch

import frappe

from barriofarma_app.barriofarma_app.utils.stock_reconciliation_negative_ledger import (
	collect_negative_ledger_blocks,
	detail_lines,
	enforce_negative_ledger_on_submit,
	headline,
)


class TestStockReconciliationNegativeLedger(unittest.TestCase):
	def test_detail_explica_saldo_comprobante_ausente_y_entrada_anterior(self):
		lines = detail_lines(
			[
				{
					"idx": 1,
					"item_code": "BF-0143",
					"item_name": "Paracetamol 500mg",
					"warehouse": "Sala de Ventas - BF",
					"qty_after": -3,
					"posting_date": "2026-09-12",
					"posting_time": "11:50:49",
					"voucher_type": "Sales Invoice",
					"voucher_no": "ACC-SINV-2026-00002",
					"voucher_missing": True,
					"target_qty": 47,
				}
			]
		)
		text = " ".join(lines)
		self.assertIn("BF-0143 (Paracetamol 500mg)", text)
		self.assertIn("Sala de Ventas - BF", text)
		self.assertIn("-3", text)
		self.assertIn("ACC-SINV-2026-00002", text)
		self.assertIn("ya no existe", text)
		self.assertIn("47", text)
		self.assertIn("anteriores", text)
		self.assertIn("3", text)

	def test_headline_repite_el_saldo_y_la_entrada_minima(self):
		text = headline(
			[
				{
					"idx": 1,
					"item_code": "BF-0143",
					"item_name": "Paracetamol 500mg",
					"warehouse": "Sala de Ventas - BF",
					"qty_after": -3,
					"posting_date": "2026-09-12",
					"posting_time": "11:50:49",
				}
			]
		)
		self.assertIn("saldo de libro -3", text)
		self.assertIn("al menos 3 unidades", text)
		self.assertNotIn("<script", text)

	def test_collect_ignora_saldo_no_negativo(self):
		with patch(
			"erpnext.stock.stock_ledger.get_previous_sle",
			return_value={"qty_after_transaction": 47},
		):
			blocks = collect_negative_ledger_blocks(
				"2026-11-02",
				"20:00:00",
				[{"idx": 1, "item_code": "BF-0143", "warehouse": "Sala de Ventas - BF", "qty": 47}],
			)
		self.assertEqual(blocks, [])

	def test_collect_marca_comprobante_inexistente(self):
		previous = {
			"qty_after_transaction": -3,
			"posting_date": "2026-09-12",
			"posting_time": "11:50:49",
			"voucher_type": "Sales Invoice",
			"voucher_no": "ACC-SINV-2026-00002",
		}
		with patch("erpnext.stock.stock_ledger.get_previous_sle", return_value=previous):
			with patch("frappe.db.get_value", return_value="Paracetamol 500mg"):
				with patch("frappe.db.exists", return_value=None):
					blocks = collect_negative_ledger_blocks(
						"2026-11-02",
						"20:00:00",
						[{"idx": 1, "item_code": "BF-0143", "warehouse": "Sala de Ventas - BF", "qty": 47}],
					)
		self.assertEqual(len(blocks), 1)
		self.assertTrue(blocks[0]["voucher_missing"])
		self.assertEqual(blocks[0]["qty_after"], -3)

	def test_submit_rechaza_con_el_aviso(self):
		doc = frappe._dict(
			purpose="Stock Reconciliation",
			posting_date="2026-11-02",
			posting_time="20:00:00",
			items=[{"idx": 1, "item_code": "BF-0143", "warehouse": "Sala de Ventas - BF", "qty": 47}],
		)
		doc._action = "submit"
		previous = {
			"qty_after_transaction": -3,
			"posting_date": "2026-09-12",
			"posting_time": "11:50:49",
			"voucher_type": "Sales Invoice",
			"voucher_no": "ACC-SINV-2026-00002",
		}
		with patch("erpnext.stock.stock_ledger.get_previous_sle", return_value=previous):
			with patch("frappe.db.get_value", return_value="Paracetamol 500mg"):
				with patch("frappe.db.exists", return_value=None):
					with patch("frappe.throw", side_effect=frappe.ValidationError) as thrown:
						with self.assertRaises(frappe.ValidationError):
							enforce_negative_ledger_on_submit(doc)
		args, kwargs = thrown.call_args
		self.assertIn("Libro de inventario en negativo", kwargs["title"])
		self.assertTrue(kwargs["as_list"])
		self.assertIn("ACC-SINV-2026-00002", " ".join(args[0]))

	def test_guardado_no_bloquea(self):
		doc = MagicMock()
		doc._action = "save"
		doc.purpose = "Stock Reconciliation"
		with patch("frappe.throw") as thrown:
			enforce_negative_ledger_on_submit(doc)
		thrown.assert_not_called()
