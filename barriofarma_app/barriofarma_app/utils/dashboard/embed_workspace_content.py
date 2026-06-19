# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# Issue: barriofarma-number-cards-platform — embed idempotente en Workspace content

import json
import uuid

from barriofarma_app.barriofarma_app.utils.dashboard.dashboard_constants import (
	CH_BF_TICKETS_DIA,
	CH_BF_VENTAS_HORA,
	LEGACY_CH_TICKETS_HORA,
	NC_BF_BOLETA,
	NC_BF_TICKETS_ULTIMA_HORA,
	NC_BF_VENTAS_ULTIMA_HORA,
)


def parse_workspace_content(content):
	if not content:
		return []
	if isinstance(content, list):
		return content
	return json.loads(content)


def content_references_widget(content_list, block_type, widget_name):
	key = "number_card_name" if block_type == "number_card" else "chart_name"
	for block in content_list:
		if block.get("type") != block_type:
			continue
		data = block.get("data") or {}
		if data.get(key) == widget_name:
			return True
	return False


def strip_widget_from_content(content_list, block_type, widget_name):
	key = "number_card_name" if block_type == "number_card" else "chart_name"
	out = []
	for block in content_list:
		if block.get("type") != block_type:
			out.append(block)
			continue
		data = block.get("data") or {}
		if data.get(key) == widget_name:
			continue
		out.append(block)
	return out


def build_block(block_type, widget_name, col=4, header_text=None):
	block_id = uuid.uuid4().hex[:10]
	if block_type == "header":
		return {
			"id": block_id,
			"type": "header",
			"data": {"text": header_text or "", "col": col},
		}
	key = "number_card_name" if block_type == "number_card" else "chart_name"
	return {
		"id": block_id,
		"type": block_type,
		"data": {key: widget_name, "col": col},
	}


def insert_blocks_after_index(content_list, blocks, insert_index):
	"""Insert blocks at insert_index (0 = start). Returns new list."""
	if insert_index < 0:
		insert_index = 0
	if insert_index > len(content_list):
		insert_index = len(content_list)
	return content_list[:insert_index] + blocks + content_list[insert_index:]


def merge_workspace_widgets(content_list, blocks_to_add):
	"""Append blocks that are not already referenced. Idempotent."""
	out = list(content_list)
	for block in blocks_to_add:
		block_type = block.get("type")
		if block_type == "header":
			text = (block.get("data") or {}).get("text", "")
			if any(
				b.get("type") == "header" and (b.get("data") or {}).get("text") == text
				for b in out
			):
				continue
			out.append(block)
			continue
		key = "number_card_name" if block_type == "number_card" else "chart_name"
		name = (block.get("data") or {}).get(key)
		if name and content_references_widget(out, block_type, name):
			continue
		out.append(block)
	return out


def selling_bf_blocks():
	header = build_block(
		"header",
		None,
		col=12,
		header_text='<span class="h4"><b>KPI POS BarrioFarma</b></span>',
	)
	return [
		header,
		build_block("number_card", NC_BF_VENTAS_ULTIMA_HORA, col=4),
		build_block("number_card", NC_BF_TICKETS_ULTIMA_HORA, col=4),
		build_block("number_card", NC_BF_BOLETA, col=4),
		build_block("chart", CH_BF_VENTAS_HORA, col=12),
		build_block("chart", CH_BF_TICKETS_DIA, col=6),
	]


def normalize_selling_bf_content(content_list):
	"""Remove legacy BF Tickets Hora chart block before merge."""
	return strip_widget_from_content(content_list, "chart", LEGACY_CH_TICKETS_HORA)
