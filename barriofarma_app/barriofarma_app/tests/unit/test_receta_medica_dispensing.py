# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Tests unitarios para dispensacion y resumen POS de Receta Medica."""

import unittest
from unittest.mock import MagicMock, patch

from barriofarma_app.barriofarma_app.doctype.receta_medica.receta_medica import RecetaMedica
from barriofarma_app.barriofarma_app.utils.domain.receta_medica_dispensing import (
	apply_invoice_qty_to_receta_items,
)
from barriofarma_app.barriofarma_app.validations.receta_medica_validation import (
	update_receta_medica_dispensation,
)


class TestRecetaMedicaDispensingStatus(unittest.TestCase):
	def _make_receta(self, **kwargs):
		doc = RecetaMedica.__new__(RecetaMedica)
		doc.status = kwargs.get("status", "Nueva")
		doc.max_dispensations = kwargs.get("max_dispensations", 6)
		doc.dispensation_count = kwargs.get("dispensation_count", 0)
		doc.items = kwargs.get("items", [])
		return doc

	def test_update_status_parcial_por_visitas(self):
		receta = self._make_receta(dispensation_count=2, max_dispensations=6)
		receta.update_status()
		self.assertEqual(receta.status, "Parcialmente Dispensada")

	def test_update_status_completada_por_visitas(self):
		receta = self._make_receta(dispensation_count=6, max_dispensations=6)
		receta.update_status()
		self.assertEqual(receta.status, "Completada")

	def test_update_status_completada_por_cantidades_item(self):
		item = MagicMock()
		item.get = lambda key, default=None: {"quantity": 6, "dispensed_qty": 6}.get(key, default)
		receta = self._make_receta(dispensation_count=1, max_dispensations=6, items=[item])
		receta.update_status()
		self.assertEqual(receta.status, "Completada")

	def test_apply_invoice_qty_to_receta_items(self):
		receta = MagicMock()
		receta_row = MagicMock()
		receta_row.get = lambda key, default=None: {
			"item": "BF-2302",
			"quantity": 6,
			"dispensed_qty": 1,
		}.get(key, default)
		receta.get = lambda key, default=None: [receta_row] if key == "items" else default

		invoice = MagicMock()
		line = MagicMock()
		line.get = lambda key, default=None: {"item_code": "BF-2302", "qty": 2}.get(key, default)
		invoice.get = lambda key, default=None: [line] if key == "items" else default

		apply_invoice_qty_to_receta_items(receta, invoice)
		self.assertEqual(receta_row.dispensed_qty, 3)

	def test_reconcile_receta_dispensed_qty_from_invoices(self):
		receta = MagicMock()
		receta.name = "RX-001"
		receta.dispensation_count = 0
		receta.status = "Nueva"
		receta.get = lambda key, default=None: getattr(receta, key, default)
		receta.save = MagicMock()
		receta.update_status = MagicMock(side_effect=lambda: setattr(receta, "status", "Parcialmente Dispensada"))

		item_row = MagicMock()
		item_row.get = lambda key, default=None: {
			"item": "BF-2302",
			"quantity": 6,
			"dispensed_qty": 0,
		}.get(key, default)
		receta.items = [item_row]

		with patch(
			"barriofarma_app.barriofarma_app.utils.domain.receta_medica_dispensing.aggregate_dispensed_qty_from_invoices",
			return_value={"BF-2302": 2},
		), patch(
			"barriofarma_app.barriofarma_app.utils.domain.receta_medica_dispensing.count_submitted_invoices_for_receta",
			return_value=2,
		), patch("frappe.db.commit"):
			from barriofarma_app.barriofarma_app.utils.domain.receta_medica_dispensing import (
				reconcile_receta_dispensed_qty,
			)

			changed = reconcile_receta_dispensed_qty(receta, persist=True)

		self.assertTrue(changed)
		self.assertEqual(item_row.dispensed_qty, 2)
		self.assertEqual(receta.dispensation_count, 2)
		receta.save.assert_called_once()

	@patch("frappe.log_error")
	@patch("frappe.db.commit")
	@patch("frappe.session")
	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_update_dispensation_usa_update_status_real(
		self, mock_exists, mock_get_doc, mock_session, mock_commit, mock_log_error
	):
		mock_session.user = "test@example.com"
		receta = self._make_receta(dispensation_count=1, max_dispensations=6)
		receta.append = MagicMock()
		receta.save = MagicMock()

		item_row = MagicMock()
		item_row.get = lambda key, default=None: {
			"item": "BF-2302",
			"quantity": 6,
			"dispensed_qty": 0,
		}.get(key, default)
		receta.items = [item_row]
		receta.get = lambda key, default=None: getattr(receta, key, default)

		mock_get_doc.return_value = receta

		invoice = MagicMock()
		invoice.custom_receta_medica = "RX-001"
		invoice.posting_date = "2026-08-13"
		invoice.name = "POS-001"
		invoice.doctype = "POS Invoice"
		inv_line = MagicMock()
		inv_line.get = lambda key, default=None: {"item_code": "BF-2302", "qty": 1}.get(key, default)
		invoice.get = lambda key, default=None: [inv_line] if key == "items" else getattr(invoice, key, default)

		update_receta_medica_dispensation(invoice)

		self.assertEqual(receta.dispensation_count, 2)
		self.assertEqual(receta.status, "Parcialmente Dispensada")
		self.assertEqual(item_row.dispensed_qty, 1)
