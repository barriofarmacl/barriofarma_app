# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para refinamiento de Receta Medica (Story 5.1)
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import getdate, today, add_days

from barriofarma_app.barriofarma_app.doctype.receta_medica.receta_medica import RecetaMedica


class TestRecetaMedicaRefinement(unittest.TestCase):
	"""Tests para refinamiento de Receta Medica"""

	def setUp(self):
		self.receta = MagicMock()
		self.receta.get = lambda key, default=None: getattr(self.receta, key, default)

	@patch('frappe.throw')
	def test_max_dispensations_debe_ser_al_menos_1(self, mock_throw):
		receta = MagicMock(spec=RecetaMedica)
		receta.get = lambda key, default=None: getattr(receta, key, default)
		receta.max_dispensations = 0
		receta.dispensation_count = 0
		RecetaMedica.validate_dispensation_limits(receta)
		mock_throw.assert_called_once()
		self.assertIn("maximo de dispensaciones debe ser al menos 1", mock_throw.call_args[0][0].lower())

	@patch('frappe.throw')
	def test_max_dispensations_valido_no_lanza_error(self, mock_throw):
		receta = MagicMock(spec=RecetaMedica)
		receta.get = lambda key, default=None: getattr(receta, key, default)
		receta.max_dispensations = 1
		receta.dispensation_count = 0
		RecetaMedica.validate_dispensation_limits(receta)
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	def test_prescription_date_obligatorio(self, mock_throw):
		receta = MagicMock(spec=RecetaMedica)
		receta.get = lambda key, default=None: getattr(receta, key, default)
		receta.prescription_date = None
		receta.valid_till = add_days(today(), 30)
		RecetaMedica.validate_temporal_validity(receta)
		mock_throw.assert_called_once()
		self.assertIn("fecha de emision", mock_throw.call_args[0][0].lower())

	@patch('frappe.throw')
	def test_valid_till_obligatorio(self, mock_throw):
		receta = MagicMock(spec=RecetaMedica)
		receta.get = lambda key, default=None: getattr(receta, key, default)
		receta.prescription_date = today()
		receta.valid_till = None
		RecetaMedica.validate_temporal_validity(receta)
		mock_throw.assert_called_once()
		self.assertIn("fecha de validez", mock_throw.call_args[0][0].lower())

	@patch('frappe.throw')
	def test_valid_till_posterior_a_prescription_date_no_lanza_error(self, mock_throw):
		receta = MagicMock(spec=RecetaMedica)
		receta.get = lambda key, default=None: getattr(receta, key, default)
		receta.prescription_date = today()
		receta.valid_till = add_days(today(), 30)
		RecetaMedica.validate_temporal_validity(receta)
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	def test_valid_till_igual_a_prescription_date_no_lanza_error(self, mock_throw):
		receta = MagicMock(spec=RecetaMedica)
		receta.get = lambda key, default=None: getattr(receta, key, default)
		prescription_date = today()
		receta.prescription_date = prescription_date
		receta.valid_till = prescription_date
		RecetaMedica.validate_temporal_validity(receta)
		mock_throw.assert_not_called()
