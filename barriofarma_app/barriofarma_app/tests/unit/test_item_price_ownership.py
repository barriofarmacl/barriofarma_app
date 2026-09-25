# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios para la propiedad de precios por tipo de lista.

Issue whiteboard #89 - change SDD barriofarma-tesoreria-precios
Spec: barriofarma-treasury-pricing R1 (propiedad de precios por tipo de lista)

Item Price es un unico DocType para compra y venta; la distincion vive en los
flags buying/selling de la Price List. Estos tests cubren la logica pura de
resolucion de dueno, sin DB.
"""

import unittest

from barriofarma_app.barriofarma_app.validations.item_price_ownership import (
    BUYING_OWNER_ROLE,
    SELLING_OWNER_ROLE,
    _is_authorized,
    _required_roles,
)


class TestRequiredRoles(unittest.TestCase):
    """R1: que rol exige cada tipo de lista."""

    def test_buying_list_requires_farmaceutico(self):
        self.assertEqual(
            _required_roles(is_buying=True, is_selling=False),
            {BUYING_OWNER_ROLE},
        )

    def test_selling_list_requires_administrativo(self):
        self.assertEqual(
            _required_roles(is_buying=False, is_selling=True),
            {SELLING_OWNER_ROLE},
        )

    def test_dual_purpose_list_requires_both_roles(self):
        self.assertEqual(
            _required_roles(is_buying=True, is_selling=True),
            {BUYING_OWNER_ROLE, SELLING_OWNER_ROLE},
        )

    def test_list_without_flags_requires_nothing(self):
        """Lista sin proposito declarado no impone dueno de precio."""
        self.assertEqual(_required_roles(is_buying=False, is_selling=False), set())


class TestIsAuthorized(unittest.TestCase):
    """R1: autorizacion efectiva a partir de los roles del usuario."""

    def test_farmaceutico_authorized_on_buying(self):
        self.assertTrue(
            _is_authorized({BUYING_OWNER_ROLE}, is_buying=True, is_selling=False)
        )

    def test_farmaceutico_denied_on_selling(self):
        self.assertFalse(
            _is_authorized({BUYING_OWNER_ROLE}, is_buying=False, is_selling=True)
        )

    def test_administrativo_authorized_on_selling(self):
        self.assertTrue(
            _is_authorized({SELLING_OWNER_ROLE}, is_buying=False, is_selling=True)
        )

    def test_administrativo_denied_on_buying(self):
        self.assertFalse(
            _is_authorized({SELLING_OWNER_ROLE}, is_buying=True, is_selling=False)
        )

    def test_dual_purpose_requires_all_roles(self):
        """Tener solo uno de los dos roles no alcanza en lista de doble proposito."""
        self.assertFalse(
            _is_authorized({SELLING_OWNER_ROLE}, is_buying=True, is_selling=True)
        )
        self.assertTrue(
            _is_authorized(
                {BUYING_OWNER_ROLE, SELLING_OWNER_ROLE}, is_buying=True, is_selling=True
            )
        )

    def test_contabilidad_denied_on_selling(self):
        """Perfil Contabilidad es variante acotada: sin escritura de precios (S12)."""
        self.assertFalse(
            _is_authorized({"Contabilidad"}, is_buying=False, is_selling=True)
        )

    def test_no_roles_denied(self):
        self.assertFalse(_is_authorized(set(), is_buying=False, is_selling=True))


class TestBypassRoles(unittest.TestCase):
    """R1: exenciones de mantenimiento."""

    def test_system_manager_bypasses_both_kinds(self):
        self.assertTrue(
            _is_authorized({"System Manager"}, is_buying=True, is_selling=False)
        )
        self.assertTrue(
            _is_authorized({"System Manager"}, is_buying=False, is_selling=True)
        )

    def test_informatica_bypasses_both_kinds(self):
        self.assertTrue(
            _is_authorized({"Informática"}, is_buying=True, is_selling=False)
        )
        self.assertTrue(
            _is_authorized({"Informática"}, is_buying=False, is_selling=True)
        )

    def test_administrator_bypasses_dual_purpose(self):
        self.assertTrue(
            _is_authorized({"Administrator"}, is_buying=True, is_selling=True)
        )


if __name__ == "__main__":
    unittest.main()
