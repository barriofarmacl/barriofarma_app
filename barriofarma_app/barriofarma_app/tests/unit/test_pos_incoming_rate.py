# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""La boleta POS copia el costo de bodega y conserva el aviso si ese costo es cero."""

import unittest

import frappe

from barriofarma_app.barriofarma_app.utils.pos_incoming_rate import (
	copy_pos_warehouse_incoming_rate,
)


def _sale(incoming_rate=0, update_stock=1, is_return=0, item_code="BF-0143", warehouse="Sala de Ventas - BF"):
	return frappe._dict(
		doctype="POS Invoice",
		is_return=is_return,
		update_stock=update_stock,
		set_warehouse=None,
		items=[
			frappe._dict(
				item_code=item_code,
				warehouse=warehouse,
				qty=1,
				rate=990,
				incoming_rate=incoming_rate,
			)
		],
	)


class TestPosIncomingRate(unittest.TestCase):
	def test_venta_copia_el_costo_de_bodega(self):
		doc = _sale()
		copy_pos_warehouse_incoming_rate(
			doc,
			rate_for_row=lambda _doc, _row, _warehouse: 280,
			is_stock_item=lambda _item: True,
		)
		row = doc.get("items")[0]
		self.assertEqual(row.incoming_rate, 280)
		self.assertEqual(row.rate, 990)

	def test_costo_cero_deja_el_aviso(self):
		doc = _sale()
		copy_pos_warehouse_incoming_rate(
			doc,
			rate_for_row=lambda _doc, _row, _warehouse: 0,
			is_stock_item=lambda _item: True,
		)
		self.assertEqual(doc.get("items")[0].incoming_rate, 0)

	def test_devolucion_no_se_toca(self):
		doc = _sale(is_return=1, incoming_rate=0)
		copy_pos_warehouse_incoming_rate(
			doc,
			rate_for_row=lambda _doc, _row, _warehouse: 280,
			is_stock_item=lambda _item: True,
		)
		self.assertEqual(doc.get("items")[0].incoming_rate, 0)

	def test_item_que_no_es_de_stock_no_se_toca(self):
		doc = _sale()
		copy_pos_warehouse_incoming_rate(
			doc,
			rate_for_row=lambda _doc, _row, _warehouse: 280,
			is_stock_item=lambda _item: False,
		)
		self.assertEqual(doc.get("items")[0].incoming_rate, 0)
