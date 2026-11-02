# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests unitarios: decisión de numeración del turno.

Issue whiteboard #90 - change SDD barriofarma-turnos-atencion
Spec: barriofarma-turnos-atencion R1 (escenarios S1, S2, S4, S5)

Aquí se aísla la única decisión no trivial del contador: cuándo confiar en
Redis y cuándo preguntarle a la base. Redis es rápido pero volátil; si se
reinicia a mitad de jornada su contador vuelve a cero y colisionaría con
turnos ya emitidos. La regla es que un `incr` que devuelve 1 es ambiguo —puede
ser inicio de día real o un Redis recién reiniciado— y solo en ese caso se
consulta la base.

El comportamiento contra base y cache reales se prueba en
tests/integration/test_turnos_atencion.py.
"""

import unittest
from unittest.mock import MagicMock, patch

from barriofarma_app.barriofarma_app.api import turnos

FECHA = "2026-09-03"


class TestSiguienteNumero(unittest.TestCase):
    """`_siguiente_numero`: Redis acelera, la base corrige."""

    def setUp(self):
        self.cache = MagicMock()
        self.patcher = patch.object(turnos.frappe, "cache", return_value=self.cache)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.cache.make_key.side_effect = lambda k: f"sitio|{k}"

    def _con_maximo(self, maximo):
        return patch.object(turnos, "_maximo_del_dia", return_value=maximo)

    # --- S1: primer turno del día -------------------------------------------

    def test_s1_dia_sin_turnos_devuelve_uno(self):
        self.cache.incr.return_value = 1

        with self._con_maximo(None):
            self.assertEqual(turnos._siguiente_numero(FECHA), 1)

    # --- S2: numeración corrida ---------------------------------------------

    def test_s2_contador_sano_no_consulta_la_base(self):
        """Camino rápido: si el contador va en 8, se devuelve 8 sin tocar la base."""
        self.cache.incr.return_value = 8

        with self._con_maximo(7) as maximo:
            self.assertEqual(turnos._siguiente_numero(FECHA), 8)
            maximo.assert_not_called()

    # --- S5: contador perdido ------------------------------------------------

    def test_s5_contador_reiniciado_se_realinea_con_la_base(self):
        """Redis devolvió 1 pero el día ya iba en 12: el turno correcto es el 13."""
        self.cache.incr.return_value = 1

        with self._con_maximo(12):
            self.assertEqual(turnos._siguiente_numero(FECHA), 13)

    def test_s5_realineacion_persiste_en_el_contador(self):
        """Sin reescribir la clave, la emisión siguiente volvería a colisionar."""
        self.cache.incr.return_value = 1

        with self._con_maximo(12):
            turnos._siguiente_numero(FECHA)

        self.cache.set.assert_called_once()
        args, _kwargs = self.cache.set.call_args
        self.assertEqual(args[1], 13)

    # --- Invariantes del manejo de la clave ----------------------------------

    def test_la_clave_lleva_prefijo_de_sitio(self):
        """Los métodos heredados de redis-py no prefijan: hay que llamar a make_key."""
        clave = turnos._clave_contador(FECHA)

        self.cache.make_key.assert_called_once()
        self.assertTrue(clave.startswith("sitio|"))
        self.assertIn(FECHA, clave)

    def test_la_clave_recibe_vencimiento(self):
        """Sin TTL, cada día dejaría una clave huérfana en Redis para siempre."""
        self.cache.incr.return_value = 3

        with self._con_maximo(2):
            turnos._siguiente_numero(FECHA)

        self.cache.expire.assert_called_once()
        args, _kwargs = self.cache.expire.call_args
        self.assertEqual(args[1], turnos.CONTADOR_TTL)

    def test_no_se_usa_la_api_serializada_del_wrapper(self):
        """`set_value` serializa con pickle y rompe el `incr` posterior."""
        self.cache.incr.return_value = 1

        with self._con_maximo(4):
            turnos._siguiente_numero(FECHA)

        self.cache.set_value.assert_not_called()
        self.cache.get_value.assert_not_called()
