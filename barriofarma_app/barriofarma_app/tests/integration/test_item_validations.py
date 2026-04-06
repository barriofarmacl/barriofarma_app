# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma
#
# Story 1.1: Tests de integracion con DB para validaciones Item (create_test_*).
# Tests con mocks del override Item viven en tests/unit/test_item_validation_overrides_mocks.py

import frappe
from frappe import _
from frappe.tests.utils import FrappeTestCase

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_shelf,
    create_test_warehouse,
)


class TestItemValidations(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.to_cleanup = {"Item": [], "Shelf": [], "Warehouse": []}

    def tearDown(self):
        frappe.set_user("Administrator")
        for doctype, names in self.to_cleanup.items():
            for name in names:
                if frappe.db.exists(doctype, name):
                    frappe.delete_doc(doctype, name, ignore_permissions=True, force=1)
        frappe.db.commit()

    def _track(self, doc):
        self.to_cleanup.setdefault(doc.doctype, [])
        self.to_cleanup[doc.doctype].append(doc.name)
        return doc

    # --- validate_control_level_invariants ---
    def test_control_level_requires_batch_expiry_and_retention(self):
        # Edge: Psicotrópico sin flags requeridos -> error
        with self.assertRaises(frappe.ValidationError):
            item = self._track(
                create_test_item(
                    item_name="CtrlEdge",
                    custom_dispensing_type="Venta Libre",
                    custom_control_level="Psicotrópico",
                    has_batch_no=0,
                    has_expiry_date=0,
                    custom_requires_prescription_retention=0,
                )
            )

        # Happy: Psicotrópico con todos los flags -> OK
        item = self._track(
            create_test_item(
                item_name="CtrlOk",
                custom_dispensing_type="Venta con Receta Retenida",
                custom_control_level="Psicotrópico",
                has_batch_no=1,
                has_expiry_date=1,
                custom_requires_prescription_retention=1,
                custom_prescription_storage_required=1,
                custom_sanitary_registration="REG-CTRL-OK",
            )
        )
        item.reload()
        self.assertTrue(item.has_batch_no and item.has_expiry_date and item.custom_requires_prescription_retention)

    # --- validate_dispensing_type_invariants ---
    def test_dispensing_type_venta_libre_adjusts_flags(self):
        # Venta Libre ajusta has_batch_no=0, custom_prescription_storage_required=0, asegura has_expiry_date=1
        item = self._track(
            create_test_item(
                item_name="VL",
                custom_dispensing_type="Venta Libre",
                has_batch_no=1,
                has_expiry_date=0,
                custom_prescription_storage_required=1,
            )
        )
        item.reload()
        self.assertEqual(item.has_batch_no, 0)
        self.assertEqual(item.custom_prescription_storage_required, 0)
        self.assertEqual(item.has_expiry_date, 1)

    def test_dispensing_type_receta_retenida_requires_batch_and_expiry(self):
        # Edge: Receta Retenida sin has_batch_no -> error
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="RR-edge1",
                    custom_dispensing_type="Venta con Receta Retenida",
                    has_batch_no=0,
                    has_expiry_date=1,
                    custom_prescription_storage_required=1,
                    custom_sanitary_registration="REG-OK-1",
                )
            )

        # Edge: Receta Retenida sin has_expiry_date -> error
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="RR-edge2",
                    custom_dispensing_type="Venta con Receta Retenida",
                    has_batch_no=1,
                    has_expiry_date=0,
                    custom_prescription_storage_required=1,
                    custom_sanitary_registration="REG-OK-2",
                )
            )

        # Happy: Receta Retenida con ambos flags -> OK (y storage_required se fuerza a 1 si faltaba)
        item = self._track(
            create_test_item(
                item_name="RR-ok",
                custom_dispensing_type="Venta con Receta Retenida",
                has_batch_no=1,
                has_expiry_date=1,
                custom_prescription_storage_required=0,
                custom_sanitary_registration="REG-OK-3",
            )
        )
        item.reload()
        self.assertEqual(item.has_batch_no, 1)
        self.assertEqual(item.has_expiry_date, 1)
        self.assertEqual(item.custom_prescription_storage_required, 1)

    # --- validate_sanitary_registration_required ---
    def test_sanitary_registration_required_for_receta_retenida(self):
        # Edge: falta registro sanitario
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="RR-no-reg",
                    custom_dispensing_type="Venta con Receta Retenida",
                    has_batch_no=1,
                    has_expiry_date=1,
                    custom_prescription_storage_required=1,
                    custom_sanitary_registration="",
                )
            )

        # Happy: con registro sanitario
        item = self._track(
            create_test_item(
                item_name="RR-reg-ok",
                custom_dispensing_type="Venta con Receta Retenida",
                has_batch_no=1,
                has_expiry_date=1,
                custom_prescription_storage_required=1,
                custom_sanitary_registration="REG-OK-4",
            )
        )
        self.assertTrue(bool(item.custom_sanitary_registration))

    # --- validate_shelf_locations_invariants ---
    def test_shelf_locations_only_one_preferred_and_compatibility(self):
        # Preparar warehouse y shelves
        wh = self._track(create_test_warehouse(f"WH-IT-{frappe.generate_hash(6)}"))
        shelf_norm = self._track(create_test_shelf(shelf_name=f"SHELF-NORM-{frappe.generate_hash(6)}", warehouse=wh.name))
        shelf_ctrl = self._track(create_test_shelf(shelf_name=f"SHELF-CTRL-{frappe.generate_hash(6)}", warehouse=wh.name, shelf_type="Controlado"))

        # Edge: dos ubicaciones preferidas -> error
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="TwoPref",
                    custom_shelf_locations=[
                        {"shelf": shelf_norm.name, "preferred_location": 1},
                        {"shelf": shelf_ctrl.name, "preferred_location": 1},
                    ],
                )
            )

        # Edge: shelf tipo Controlado con item sin control_level -> error
        with self.assertRaises(frappe.ValidationError):
            self._track(
                create_test_item(
                    item_name="CtrlShelfNoLevel",
                    custom_dispensing_type="Venta Libre",
                    custom_shelf_locations=[{"shelf": shelf_ctrl.name, "preferred_location": 1}],
                )
            )

        # Happy: shelf tipo Controlado con control_level válido -> OK
        item = self._track(
            create_test_item(
                item_name="CtrlShelfOk",
                custom_dispensing_type="Venta Libre",
                custom_control_level="Psicotrópico",
                has_batch_no=1,
                has_expiry_date=1,
                custom_requires_prescription_retention=1,
                custom_shelf_locations=[{"shelf": shelf_ctrl.name, "preferred_location": 1}],
            )
        )
        self.assertTrue(frappe.db.exists("Item", item.name))

