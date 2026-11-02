# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests de integración: superficie de acceso del kiosco de turnos.

Issue whiteboard #90 - change SDD barriofarma-turnos-atencion
Spec: barriofarma-turnos-atencion R4 (escenarios S13, S14, S15, S16)

La tablet del kiosco vive en la entrada del local, con sesión persistente y sin
supervisión: es la superficie físicamente más accesible de la instalación. Su
rol se diseñó para que robarla o manipularla sea un incidente de bajo impacto.

`Kiosco Turnos` recibe `create` pero no `write`. Eso no es una sutileza: llamar
al siguiente y marcar ausente son escrituras sobre turnos existentes, así que
quedan fuera por construcción, sin depender de una guarda explícita en el
código de la API que alguien podría olvidar al agregar un método nuevo.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from barriofarma_app.barriofarma_app.api import turnos
from barriofarma_app.barriofarma_app.utils.permissions.setup_permissions import (
    setup_permissions_for_role,
)
from barriofarma_app.barriofarma_app.utils.permissions.setup_roles import create_custom_roles

DOCTYPE = "Turno Atencion"
ROL_KIOSCO = "Kiosco Turnos"

USUARIO_KIOSCO = "kiosco.turnos.test@barriofarma.cl"
USUARIO_AUXILIAR = "auxiliar.turnos.test@barriofarma.cl"

# Documentos que el kiosco no debe poder mirar bajo ninguna circunstancia.
DOCTYPES_VEDADOS = ("POS Invoice", "Item", "Receta Medica")


def _usuario_con_roles(email, roles):
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

    for rol in roles:
        user.append("roles", {"role": rol})

    user.save(ignore_permissions=True)
    frappe.db.commit()
    return email


class TestSuperficieDelKiosco(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        create_custom_roles()
        setup_permissions_for_role(ROL_KIOSCO)
        frappe.db.commit()

        cls.kiosco = _usuario_con_roles(USUARIO_KIOSCO, [ROL_KIOSCO])
        cls.auxiliar = _usuario_con_roles(USUARIO_AUXILIAR, ["Auxiliar"])

    def setUp(self):
        frappe.set_user("Administrator")
        self.fecha = today()
        frappe.db.delete(DOCTYPE, {"fecha": self.fecha})
        frappe.db.commit()
        frappe.cache().delete(turnos._clave_contador(self.fecha))

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.delete(DOCTYPE, {"fecha": self.fecha})
        frappe.db.commit()

    def _sembrar(self, numero, estado="Esperando"):
        frappe.get_doc(
            {"doctype": DOCTYPE, "fecha": self.fecha, "numero": numero, "estado": estado}
        ).insert(ignore_permissions=True)
        frappe.db.commit()

    # --- El rol existe y no toca el escritorio ---------------------------------

    def test_el_rol_del_kiosco_no_tiene_acceso_al_desk(self):
        """Una tablet desatendida no debe poder entrar a /app."""
        self.assertTrue(frappe.db.exists("Role", ROL_KIOSCO))
        self.assertEqual(frappe.db.get_value("Role", ROL_KIOSCO, "desk_access"), 0)

    # --- S13: el kiosco emite ---------------------------------------------------

    def test_s13_el_kiosco_puede_emitir(self):
        frappe.set_user(self.kiosco)

        self.assertEqual(turnos.emitir_turno()["numero"], 1)

    # --- S14: el kiosco no avanza la cola ---------------------------------------

    def test_s14_el_kiosco_no_puede_llamar_al_siguiente(self):
        self._sembrar(1)
        frappe.set_user(self.kiosco)

        with self.assertRaises(frappe.PermissionError):
            turnos.llamar_siguiente()

    def test_s14_el_kiosco_no_puede_marcar_ausente(self):
        self._sembrar(1, estado="Llamado")
        frappe.set_user(self.kiosco)

        with self.assertRaises(frappe.PermissionError):
            turnos.marcar_ausente()

    def test_s14_el_kiosco_no_tiene_write_sobre_turnos(self):
        """La causa raíz de S14: sin `write`, ninguna operación de avance es posible."""
        frappe.set_user(self.kiosco)

        self.assertTrue(frappe.has_permission(DOCTYPE, "create"))
        self.assertFalse(frappe.has_permission(DOCTYPE, "write"))
        self.assertFalse(frappe.has_permission(DOCTYPE, "delete"))

    # --- S15: el kiosco no ve el negocio ----------------------------------------

    def test_s15_el_kiosco_no_accede_a_documentos_del_negocio(self):
        frappe.set_user(self.kiosco)

        for doctype in DOCTYPES_VEDADOS:
            with self.subTest(doctype=doctype):
                self.assertFalse(
                    frappe.has_permission(doctype, "read"),
                    f"El kiosco puede leer {doctype}",
                )

    def test_s15_el_kiosco_no_puede_listar_documentos_del_negocio(self):
        """`get_all` ignora permisos; `get_list` es el intento real de lectura."""
        frappe.set_user(self.kiosco)

        for doctype in DOCTYPES_VEDADOS:
            with self.subTest(doctype=doctype):
                with self.assertRaises(frappe.PermissionError):
                    frappe.get_list(doctype, limit=1, ignore_permissions=False)

    # --- S16: el cajero sí opera la cola ------------------------------------------

    def test_s16_el_auxiliar_llama_y_marca_ausente(self):
        self._sembrar(1)
        self._sembrar(2)
        frappe.set_user(self.auxiliar)

        self.assertEqual(turnos.llamar_siguiente()["numero"], 1)
        self.assertTrue(turnos.marcar_ausente()["ok"])

    def test_s16_el_auxiliar_tambien_puede_emitir(self):
        """Si el kiosco falla, el mostrador debe poder entregar el número."""
        frappe.set_user(self.auxiliar)

        self.assertEqual(turnos.emitir_turno()["numero"], 1)
