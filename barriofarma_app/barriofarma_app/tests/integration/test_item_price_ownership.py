# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests de integración: propiedad de precios repartida por tipo de lista.

Issue whiteboard #89 - change SDD barriofarma-tesoreria-precios
Spec: barriofarma-treasury-pricing, escenarios S1-S7 y S11-S13

La autorización se resuelve en dos capas independientes:
- Capa 1 (DocPerm): quién puede tocar `Item Price` en absoluto.
- Capa 2 (dominio): sobre qué tipo de lista, según los flags buying/selling.

Ambas son necesarias, así que los tests cubren también el caso de defensa en
profundidad: tener solo una de las dos no alcanza.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

BUYING_LIST = "Standard Buying"
SELLING_LIST = "Standard Selling"


def _ensure_user(email, roles):
    """Crea (o reutiliza) un usuario de test con exactamente los roles indicados."""
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
        user.set("roles", [])
    else:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": email.split("@")[0],
                "send_welcome_email": 0,
            }
        )

    for role in roles:
        if frappe.db.exists("Role", role):
            user.append("roles", {"role": role})

    user.flags.ignore_permissions = True
    user.save(ignore_permissions=True)
    frappe.db.commit()
    return user


def _make_item():
    """Item mínimo creado como Administrator, para colgarle precios."""
    item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
    item = frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": f"TEST-PRICE-OWN-{frappe.generate_hash(length=8)}",
            "item_name": "Item propiedad de precios",
            "item_group": item_group,
            "stock_uom": "Unit",
            "is_stock_item": 0,
        }
    )
    item.insert(ignore_permissions=True)
    frappe.db.commit()
    return item.name


def _item_price(item_code, price_list, rate=1000):
    return frappe.get_doc(
        {
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": price_list,
            "price_list_rate": rate,
        }
    )


class TestItemPriceOwnership(FrappeTestCase):
    """R1: compra = Farmacéutico, venta = Administración."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.farmaceutico = _ensure_user(
            "test_price_farm@test.barriofarma.cl", ["Farmacéutico"]
        )
        # Perfil Administrativo completo: rol custom (capa 2) + portador de permisos (capa 1)
        cls.administrativo = _ensure_user(
            "test_price_admin@test.barriofarma.cl",
            ["Administrativo", "Purchase Master Manager"],
        )
        cls.contabilidad = _ensure_user(
            "test_price_conta@test.barriofarma.cl",
            ["Contabilidad", "Accounts Manager"],
        )
        # Solo capa 1: permiso de DocType sin el rol de dominio
        cls.solo_docperm = _ensure_user(
            "test_price_pmm@test.barriofarma.cl", ["Purchase Master Manager"]
        )

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def test_s1_farmaceutico_writes_buying_price(self):
        """S1: el Farmacéutico fija el precio de compra."""
        item_code = _make_item()
        frappe.set_user(self.farmaceutico.name)

        doc = _item_price(item_code, BUYING_LIST)
        doc.insert()

        self.assertTrue(doc.name)
        self.assertEqual(doc.price_list, BUYING_LIST)

    def test_s2_farmaceutico_denied_on_selling_price(self):
        """S2: el Farmacéutico no fija el precio de venta."""
        item_code = _make_item()
        frappe.set_user(self.farmaceutico.name)

        doc = _item_price(item_code, SELLING_LIST)
        with self.assertRaises(frappe.ValidationError) as ctx:
            doc.insert()

        self.assertIn("Administración", str(ctx.exception))

    def test_s3_administrativo_writes_selling_price(self):
        """S3: Administración fija el precio de venta."""
        item_code = _make_item()
        frappe.set_user(self.administrativo.name)

        doc = _item_price(item_code, SELLING_LIST)
        doc.insert()

        self.assertTrue(doc.name)
        self.assertEqual(doc.price_list, SELLING_LIST)

    def test_s4_administrativo_denied_on_buying_price(self):
        """S4: Administración no altera el precio de compra."""
        item_code = _make_item()
        frappe.set_user(self.administrativo.name)

        doc = _item_price(item_code, BUYING_LIST)
        with self.assertRaises(frappe.ValidationError) as ctx:
            doc.insert()

        self.assertIn("Farmacéutico", str(ctx.exception))

    def test_s5_administrativo_reads_buying_price(self):
        """S5: la lectura del costo queda abierta, es insumo del margen."""
        item_code = _make_item()
        frappe.set_user("Administrator")
        price = _item_price(item_code, BUYING_LIST)
        price.insert(ignore_permissions=True)

        frappe.set_user(self.administrativo.name)
        self.assertTrue(
            frappe.has_permission("Item Price", ptype="read", doc=price.name)
        )

    def test_s12_contabilidad_denied_on_selling_price(self):
        """S12: Contabilidad es variante acotada, sin escritura de precios."""
        item_code = _make_item()
        frappe.set_user(self.contabilidad.name)

        doc = _item_price(item_code, SELLING_LIST)
        with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
            doc.insert()

    def test_docperm_without_domain_role_is_denied(self):
        """Defensa en profundidad: la capa 1 sin la capa 2 no alcanza."""
        item_code = _make_item()
        frappe.set_user(self.solo_docperm.name)

        doc = _item_price(item_code, SELLING_LIST)
        with self.assertRaises(frappe.ValidationError) as ctx:
            doc.insert()

        self.assertIn("Administración", str(ctx.exception))

    def test_bypass_role_writes_any_list(self):
        """Informática y System Manager quedan exentos para mantenimiento."""
        item_code = _make_item()
        frappe.set_user("Administrator")

        for price_list in (BUYING_LIST, SELLING_LIST):
            with self.subTest(price_list=price_list):
                doc = _item_price(item_code, price_list)
                doc.insert()
                self.assertTrue(doc.name)


class TestItemStandardRateGuard(FrappeTestCase):
    """R2: alta de catálogo sin PermissionError opaco."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.farmaceutico = _ensure_user(
            "test_price_farm@test.barriofarma.cl", ["Farmacéutico"]
        )
        cls.item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def _new_item_doc(self, standard_rate=None):
        payload = {
            "doctype": "Item",
            "item_code": f"TEST-STDRATE-{frappe.generate_hash(length=8)}",
            "item_name": "Item alta catalogo",
            "item_group": self.item_group,
            "stock_uom": "Unit",
            "is_stock_item": 0,
        }
        if standard_rate is not None:
            payload["standard_rate"] = standard_rate
        return frappe.get_doc(payload)

    def test_s6_farmaceutico_creates_item_without_standard_rate(self):
        """S6: el alta sin precio estándar se completa y no crea Item Price."""
        frappe.set_user(self.farmaceutico.name)

        item = self._new_item_doc()
        item.insert()

        self.assertTrue(item.name)
        self.assertFalse(
            frappe.db.exists("Item Price", {"item_code": item.name, "price_list": SELLING_LIST})
        )

    def test_s7_farmaceutico_with_standard_rate_gets_domain_error(self):
        """S7: con precio estándar recibe mensaje de dominio, no PermissionError."""
        frappe.set_user(self.farmaceutico.name)

        item = self._new_item_doc(standard_rate=1500)
        with self.assertRaises(frappe.ValidationError) as ctx:
            item.insert()

        message = str(ctx.exception)
        self.assertIn("Administración", message)
        self.assertNotIsInstance(ctx.exception, frappe.PermissionError)


class TestPricingBoundaries(FrappeTestCase):
    """R5: fronteras que no cambian."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.terreno = _ensure_user(
            "test_price_terreno@test.barriofarma.cl", ["Vendedor Terreno"]
        )
        cls.bodeguero = _ensure_user(
            "test_price_bodega@test.barriofarma.cl", ["Bodeguero"]
        )

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def test_s11_vendedor_terreno_reads_but_does_not_write_prices(self):
        """S11: el catálogo terreno sigue leyendo precios, sin escribirlos."""
        frappe.set_user(self.terreno.name)

        for doctype in ("Item Price", "Price List"):
            with self.subTest(doctype=doctype):
                self.assertTrue(frappe.has_permission(doctype, ptype="read"))
                self.assertFalse(frappe.has_permission(doctype, ptype="write"))

    def test_s13_bodeguero_cannot_create_supplier(self):
        """S13: el Bodeguero prepara y despacha, no administra proveedores."""
        frappe.set_user(self.bodeguero.name)

        self.assertTrue(frappe.has_permission("Supplier", ptype="read"))
        self.assertFalse(frappe.has_permission("Supplier", ptype="create"))
        self.assertFalse(frappe.has_permission("Supplier", ptype="write"))
