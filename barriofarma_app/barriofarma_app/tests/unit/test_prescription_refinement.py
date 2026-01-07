# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para refinamiento de Prescription (Story 5.1)
"""

import unittest
from unittest.mock import MagicMock, patch
import frappe
from frappe import _
from frappe.exceptions import ValidationError
from frappe.utils import getdate, today, add_days


class TestPrescriptionRefinement(unittest.TestCase):
	"""Tests para refinamiento de Prescription"""

	def setUp(self):
		self.prescription = MagicMock()
		self.prescription.get = lambda key, default=None: getattr(self.prescription, key, default)

	@patch('frappe.throw')
	def test_max_dispensations_debe_ser_al_menos_1(self, mock_throw):
		"""Test: max_dispensations debe ser al menos 1"""
		from barriofarma_app.barriofarma_app.doctype.prescription.prescription import Prescription
		
		prescription = MagicMock(spec=Prescription)
		prescription.get = lambda key, default=None: getattr(prescription, key, default)
		prescription.max_dispensations = 0
		prescription.dispensation_count = 0
		
		# Llamar directamente al método
		Prescription.validate_dispensation_limits(prescription)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("máximo de dispensaciones debe ser al menos 1", call_args.lower())

	@patch('frappe.throw')
	def test_max_dispensations_valido_no_lanza_error(self, mock_throw):
		"""Test: max_dispensations >= 1 no lanza error"""
		from barriofarma_app.barriofarma_app.doctype.prescription.prescription import Prescription
		
		prescription = MagicMock(spec=Prescription)
		prescription.get = lambda key, default=None: getattr(prescription, key, default)
		prescription.max_dispensations = 1
		prescription.dispensation_count = 0
		
		Prescription.validate_dispensation_limits(prescription)
		
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	def test_prescription_date_obligatorio(self, mock_throw):
		"""Test: prescription_date es obligatorio"""
		from barriofarma_app.barriofarma_app.doctype.prescription.prescription import Prescription
		
		prescription = MagicMock(spec=Prescription)
		prescription.get = lambda key, default=None: getattr(prescription, key, default)
		prescription.prescription_date = None
		prescription.valid_till = add_days(today(), 30)
		
		Prescription.validate_temporal_validity(prescription)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("fecha de emisión", call_args.lower())

	@patch('frappe.throw')
	def test_valid_till_obligatorio(self, mock_throw):
		"""Test: valid_till es obligatorio"""
		from barriofarma_app.barriofarma_app.doctype.prescription.prescription import Prescription
		
		prescription = MagicMock(spec=Prescription)
		prescription.get = lambda key, default=None: getattr(prescription, key, default)
		prescription.prescription_date = today()
		prescription.valid_till = None
		
		Prescription.validate_temporal_validity(prescription)
		
		mock_throw.assert_called_once()
		call_args = mock_throw.call_args[0][0]
		self.assertIn("fecha de validez", call_args.lower())

	@patch('frappe.throw')
	def test_valid_till_posterior_a_prescription_date_no_lanza_error(self, mock_throw):
		"""Test: valid_till posterior a prescription_date no lanza error"""
		from barriofarma_app.barriofarma_app.doctype.prescription.prescription import Prescription
		
		prescription = MagicMock(spec=Prescription)
		prescription.get = lambda key, default=None: getattr(prescription, key, default)
		prescription.prescription_date = today()
		prescription.valid_till = add_days(today(), 30)
		
		Prescription.validate_temporal_validity(prescription)
		
		mock_throw.assert_not_called()

	@patch('frappe.throw')
	def test_valid_till_igual_a_prescription_date_no_lanza_error(self, mock_throw):
		"""Test: valid_till igual a prescription_date no lanza error"""
		from barriofarma_app.barriofarma_app.doctype.prescription.prescription import Prescription
		
		prescription = MagicMock(spec=Prescription)
		prescription.get = lambda key, default=None: getattr(prescription, key, default)
		prescription_date = today()
		prescription.prescription_date = prescription_date
		prescription.valid_till = prescription_date
		
		Prescription.validate_temporal_validity(prescription)
		
		mock_throw.assert_not_called()

