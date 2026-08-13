# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Tests enrich POS items con flags receta retenida."""

import unittest
from unittest.mock import patch

from barriofarma_app.barriofarma_app.api.pos_items import (
	_enrich_get_items_response,
	enrich_pos_items,
)


class TestEnrichPosItems(unittest.TestCase):
	@patch("barriofarma_app.barriofarma_app.api.pos_items.frappe.get_all")
	def test_enrich_marks_receta_retenida(self, mock_get_all):
		mock_get_all.return_value = [
			{
				"name": "BF-2302",
				"custom_dispensing_type": "Venta con Receta Retenida",
				"custom_requires_prescription_retention": 1,
			}
		]
		items = [{"item_code": "BF-2302", "item_name": "Zopiclona"}]
		result = enrich_pos_items(items)
		self.assertEqual(result[0]["requires_receta_retenida"], 1)
		self.assertEqual(result[0]["custom_dispensing_type"], "Venta con Receta Retenida")

	@patch("barriofarma_app.barriofarma_app.api.pos_items.frappe.get_all")
	def test_enrich_venta_libre_not_flagged(self, mock_get_all):
		mock_get_all.return_value = [
			{
				"name": "VL-001",
				"custom_dispensing_type": "Venta Libre",
				"custom_requires_prescription_retention": 0,
			}
		]
		items = [{"item_code": "VL-001", "item_name": "Paracetamol"}]
		result = enrich_pos_items(items)
		self.assertEqual(result[0]["requires_receta_retenida"], 0)

	def test_enrich_empty_list(self):
		self.assertEqual(enrich_pos_items([]), [])
		self.assertEqual(enrich_pos_items(None), [])

	@patch("barriofarma_app.barriofarma_app.api.pos_items.enrich_pos_items")
	def test_enrich_dict_response_v16(self, mock_enrich):
		mock_enrich.return_value = [{"item_code": "BF-2302", "requires_receta_retenida": 1}]
		payload = {"items": [{"item_code": "BF-2302"}]}
		result = _enrich_get_items_response(payload)
		self.assertIn("items", result)
		mock_enrich.assert_called_once_with([{"item_code": "BF-2302"}])
		self.assertEqual(result["items"][0]["requires_receta_retenida"], 1)
