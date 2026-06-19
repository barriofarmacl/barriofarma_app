# -*- coding: utf-8 -*-
# Issue: barriofarma-number-cards-platform

import json
import unittest

from barriofarma_app.barriofarma_app.utils.dashboard.embed_workspace_content import (
	content_references_widget,
	merge_workspace_widgets,
	parse_workspace_content,
	selling_bf_blocks,
)


class TestEmbedWorkspaceContent(unittest.TestCase):
	def test_parse_workspace_content_empty(self):
		self.assertEqual(parse_workspace_content(None), [])
		self.assertEqual(parse_workspace_content(""), [])

	def test_content_references_number_card(self):
		content = [{"type": "number_card", "data": {"number_card_name": "BF Boleta Promedio", "col": 4}}]
		self.assertTrue(content_references_widget(content, "number_card", "BF Boleta Promedio"))
		self.assertFalse(content_references_widget(content, "number_card", "Other"))

	def test_merge_idempotent(self):
		content = []
		blocks = selling_bf_blocks()
		first = merge_workspace_widgets(content, blocks)
		second = merge_workspace_widgets(first, blocks)
		self.assertEqual(len(first), len(second))
		names = [
			b["data"].get("number_card_name") or b["data"].get("chart_name")
			for b in second
			if b["type"] != "header"
		]
		self.assertIn("BF Ventas Última Hora", names)
		self.assertIn("BF Tickets Última Hora", names)
		self.assertIn("BF Boleta Promedio", names)
		self.assertIn("BF Ventas por Hora", names)
		self.assertIn("BF Tickets Día", names)

	def test_merge_does_not_duplicate_chart(self):
		content = [{"type": "chart", "data": {"chart_name": "BF Tickets Día", "col": 6}}]
		blocks = selling_bf_blocks()
		merged = merge_workspace_widgets(content, blocks)
		chart_count = sum(
			1
			for b in merged
			if b.get("type") == "chart" and b.get("data", {}).get("chart_name") == "BF Tickets Día"
		)
		self.assertEqual(chart_count, 1)

	def test_selling_bf_blocks_json_serializable(self):
		json.dumps(selling_bf_blocks())
