# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests de integración: endpoint público de la pantalla de sala.

Issue whiteboard #90 - change SDD barriofarma-turnos-atencion
Spec: barriofarma-turnos-atencion R3 (escenarios S10, S11, S12)

`turno_en_atencion` y `esperar_turno_en_atencion` son los metodos con `allow_guest=True`.
Un monitor de sala no tiene sesión, así que la alternativa sería embeber
credenciales en un dispositivo desatendido, que es peor.

El test que importa aquí es S11. Afirma sobre el **conjunto exacto** de claves
de la respuesta, no sobre la ausencia de algunas: si mañana alguien devuelve el
documento completo con `as_dict()`, un `assertNotIn` puntual no lo detectaría y
la comparación de conjuntos sí. El endpoint es público, así que cada campo que
se filtre es información operativa de la farmacia expuesta sin autenticación.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today
from unittest.mock import patch

from barriofarma_app.barriofarma_app.api import turnos

DOCTYPE = "Turno Atencion"

CLAVES_PERMITIDAS = {"numero", "desde"}


class TestTurnoEnAtencionPublico(FrappeTestCase):
    def setUp(self):
        self.fecha = today()
        self.usuario_original = frappe.session.user
        frappe.set_user("Administrator")
        frappe.db.delete(DOCTYPE, {"fecha": self.fecha})
        frappe.db.commit()

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.delete(DOCTYPE, {"fecha": self.fecha})
        frappe.db.commit()
        frappe.cache().delete_value(turnos.CLAVE_PANTALLA)
        frappe.set_user(self.usuario_original)

    def _sembrar(self, numero, estado):
        frappe.get_doc(
            {"doctype": DOCTYPE, "fecha": self.fecha, "numero": numero, "estado": estado}
        ).insert(ignore_permissions=True)
        frappe.db.commit()

    # --- S10: el número en atención -------------------------------------------

    def test_s10_devuelve_el_numero_en_atencion(self):
        self._sembrar(12, "Llamado")

        self.assertEqual(turnos.turno_en_atencion()["numero"], 12)

    def test_s10_ignora_turnos_en_espera(self):
        """La pantalla muestra a quien se atiende, no a quien espera."""
        self._sembrar(12, "Llamado")
        self._sembrar(13, "Esperando")

        self.assertEqual(turnos.turno_en_atencion()["numero"], 12)

    # --- S11: superficie mínima -----------------------------------------------

    def test_s11_la_respuesta_solo_trae_numero_y_marca_de_tiempo(self):
        self._sembrar(12, "Llamado")

        respuesta = turnos.turno_en_atencion()

        self.assertEqual(
            set(respuesta.keys()),
            CLAVES_PERMITIDAS,
            "El endpoint público cambió su superficie: revisar qué se está exponiendo",
        )

    def test_s11_no_expone_identidad_del_operador(self):
        """`llamado_por` es un correo de trabajador: no sale por un endpoint público."""
        self._sembrar(12, "Llamado")
        frappe.db.set_value(
            DOCTYPE,
            {"fecha": self.fecha, "numero": 12},
            "llamado_por",
            "Administrator",
        )
        frappe.db.commit()

        respuesta = turnos.turno_en_atencion()

        self.assertNotIn("llamado_por", respuesta)
        self.assertNotIn("Administrator", str(respuesta))

    def test_s11_no_expone_el_largo_de_la_cola(self):
        """Cuánta gente espera es información operativa, no del cliente."""
        for numero in range(20, 25):
            self._sembrar(numero, "Esperando")
        self._sembrar(12, "Llamado")

        respuesta = turnos.turno_en_atencion()

        self.assertEqual(set(respuesta.keys()), CLAVES_PERMITIDAS)

    # --- S12: sala sin atención en curso ---------------------------------------

    def test_s12_sin_turno_llamado_devuelve_vacio(self):
        self._sembrar(3, "Esperando")

        self.assertEqual(turnos.turno_en_atencion(), {})

    def test_s12_dia_sin_turnos_no_lanza_error(self):
        try:
            respuesta = turnos.turno_en_atencion()
        except Exception as exc:
            self.fail(f"La pantalla no debe recibir un error: {exc}")

        self.assertEqual(respuesta, {})

    # --- Acceso sin sesión ------------------------------------------------------

    def test_guest_puede_consultar(self):
        self._sembrar(12, "Llamado")

        frappe.set_user("Guest")
        respuesta = turnos.turno_en_atencion()

        self.assertEqual(respuesta["numero"], 12)

    def test_esperar_devuelve_al_tiro_si_el_visto_no_coincide(self):
        """No espera los 55 s cuando la TV aun no tiene el numero actual."""
        self._sembrar(12, "Llamado")
        frappe.cache().delete_value(turnos.CLAVE_PANTALLA)

        frappe.set_user("Guest")
        respuesta = turnos.esperar_turno_en_atencion(visto="")

        self.assertEqual(respuesta["numero"], 12)
        self.assertEqual(set(respuesta.keys()), CLAVES_PERMITIDAS)

    def test_esperar_timeout_si_el_visto_ya_es_el_actual(self):
        self._sembrar(12, "Llamado")
        frappe.cache().delete_value(turnos.CLAVE_PANTALLA)
        actual = turnos.turno_en_atencion()
        visto = turnos._token_pantalla(actual)

        with patch.object(turnos, "ESPERA_PANTALLA_S", 0), patch.object(
            turnos, "ESPERA_PANTALLA_PASO_S", 0
        ):
            respuesta = turnos.esperar_turno_en_atencion(visto=visto)

        self.assertEqual(respuesta["numero"], 12)

    def test_solo_la_consulta_de_pantalla_es_publica(self):
        """El resto del módulo escribe: ninguno de esos métodos puede ser público."""
        self.assertIn(turnos.turno_en_atencion, frappe.guest_methods)
        self.assertIn(turnos.esperar_turno_en_atencion, frappe.guest_methods)

        for metodo in (turnos.emitir_turno, turnos.llamar_siguiente, turnos.marcar_ausente):
            self.assertNotIn(metodo, frappe.guest_methods, f"{metodo.__name__} quedó público")

    def test_guest_no_puede_emitir(self):
        """El kiosco tiene usuario propio: emitir no es una operación anónima (R4)."""
        frappe.set_user("Guest")

        with self.assertRaises(Exception):
            turnos.emitir_turno()
