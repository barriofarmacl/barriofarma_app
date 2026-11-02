# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Tests de integración: agregado Turno Atencion.

Issue whiteboard #90 - change SDD barriofarma-turnos-atencion
Spec: barriofarma-turnos-atencion

El turno es orden de atención, no transacción comercial. Dos cosas se prueban
aquí y ninguna es negociable:

- La frontera del agregado (S17): el turno no toca documentos comerciales ni
  datos personales. Se verifica sobre el metadato, no sobre una lista fija de
  nombres, para que un campo agregado mañana también quede cubierto.
- La unicidad de `(fecha, numero)` la impone la base de datos vía clave
  primaria compuesta. Es el invariante crítico del agregado: si esto cede, dos
  clientes reciben el mismo número.
"""

import threading
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from barriofarma_app.barriofarma_app.api import turnos

DOCTYPE = "Turno Atencion"

# Documentos y entidades que el turno no debe referenciar (spec R5).
DOCTYPES_PROHIBIDOS = {
    "POS Invoice",
    "Sales Invoice",
    "Delivery Note",
    "Receta Medica",
    "Patient",
    "Customer",
}


def _limpiar_turnos(fecha):
    frappe.db.delete(DOCTYPE, {"fecha": fecha})
    frappe.db.commit()
    frappe.cache().delete(turnos._clave_contador(fecha))


def _sembrar(fecha, numero, estado="Esperando"):
    doc = frappe.get_doc(
        {"doctype": DOCTYPE, "fecha": fecha, "numero": numero, "estado": estado}
    ).insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


class TestTurnoAtencionAgregado(FrappeTestCase):
    """Frontera del agregado y garantía de unicidad en base de datos."""

    def setUp(self):
        self.fecha = today()
        _limpiar_turnos(self.fecha)

    def tearDown(self):
        _limpiar_turnos(self.fecha)

    # --- S17: el turno no se acopla al negocio -------------------------------

    def test_s17_sin_referencia_a_documento_comercial(self):
        """Ningún Link del DocType apunta a un documento comercial ni a una persona."""
        meta = frappe.get_meta(DOCTYPE)

        referencias = {
            f.options
            for f in meta.fields
            if f.fieldtype in ("Link", "Dynamic Link") and f.options
        }

        prohibidas = referencias & DOCTYPES_PROHIBIDOS
        self.assertEqual(
            prohibidas,
            set(),
            f"El turno referencia documentos fuera de su agregado: {prohibidas}",
        )

    def test_s17_sin_campos_de_dato_personal(self):
        """No hay campos para nombre, RUT ni contacto: el kiosco no captura identidad."""
        meta = frappe.get_meta(DOCTYPE)
        fieldnames = {f.fieldname for f in meta.fields}

        sospechosos = {
            fn
            for fn in fieldnames
            if any(t in fn for t in ("rut", "nombre", "name", "cliente", "customer",
                                     "patient", "telefono", "phone", "email"))
        }
        # `llamado_por` es el operador, no el cliente; no aplica.
        sospechosos -= {"llamado_por"}

        self.assertEqual(
            sospechosos,
            set(),
            f"El turno tiene campos que parecen dato personal del cliente: {sospechosos}",
        )

    # --- Invariante: la base garantiza la unicidad ---------------------------

    def test_par_fecha_numero_es_unico_en_base_de_datos(self):
        """Insertar dos veces el mismo (fecha, numero) debe fallar en la base, no en Python."""
        primero = frappe.get_doc(
            {"doctype": DOCTYPE, "fecha": self.fecha, "numero": 1, "estado": "Esperando"}
        ).insert(ignore_permissions=True)
        frappe.db.commit()

        self.assertTrue(primero.name)

        duplicado = frappe.get_doc(
            {"doctype": DOCTYPE, "fecha": self.fecha, "numero": 1, "estado": "Esperando"}
        )

        with self.assertRaises(frappe.DuplicateEntryError):
            duplicado.insert(ignore_permissions=True)

        frappe.db.rollback()

    def test_name_codifica_fecha_y_numero(self):
        """El `name` es la clave del invariante: debe derivarse de (fecha, numero)."""
        turno = frappe.get_doc(
            {"doctype": DOCTYPE, "fecha": self.fecha, "numero": 7, "estado": "Esperando"}
        ).insert(ignore_permissions=True)

        self.assertIn(str(self.fecha), turno.name)
        self.assertTrue(turno.name.endswith("-7"))

    def test_turno_nace_esperando_y_con_marca_de_emision(self):
        """Estado inicial del ciclo de vida (spec R1)."""
        turno = frappe.get_doc(
            {"doctype": DOCTYPE, "fecha": self.fecha, "numero": 1}
        ).insert(ignore_permissions=True)

        self.assertEqual(turno.estado, "Esperando")
        self.assertIsNotNone(turno.emitido_en)


class TestEmisionDeTurno(FrappeTestCase):
    """R1 contra base y cache reales, incluida la emisión concurrente."""

    def setUp(self):
        self.fecha = today()
        _limpiar_turnos(self.fecha)

    def tearDown(self):
        _limpiar_turnos(self.fecha)
        _limpiar_turnos(add_days(self.fecha, -1))

    # --- S1, S2: numeración corrida ------------------------------------------

    def test_s1_primer_turno_del_dia_es_uno(self):
        self.assertEqual(turnos.emitir_turno()["numero"], 1)

    def test_s2_numeracion_corrida(self):
        for esperado in (1, 2, 3):
            self.assertEqual(turnos.emitir_turno()["numero"], esperado)

    def test_s1_el_turno_emitido_queda_esperando(self):
        emitido = turnos.emitir_turno()

        estado = frappe.db.get_value(
            DOCTYPE, {"fecha": self.fecha, "numero": emitido["numero"]}, "estado"
        )
        self.assertEqual(estado, "Esperando")

    # --- S4: reinicio diario --------------------------------------------------

    def test_s4_la_numeracion_reinicia_cada_dia(self):
        """El turno 42 de ayer no condiciona al primero de hoy."""
        ayer = add_days(self.fecha, -1)
        _limpiar_turnos(ayer)
        _sembrar(ayer, 42)

        self.assertEqual(turnos.emitir_turno()["numero"], 1)

    def test_s4_no_hay_barrido_de_la_jornada_anterior(self):
        """Los turnos de ayer se conservan como histórico (D2 del gate)."""
        ayer = add_days(self.fecha, -1)
        _limpiar_turnos(ayer)
        _sembrar(ayer, 42, estado="Atendido")

        turnos.emitir_turno()

        self.assertTrue(frappe.db.exists(DOCTYPE, {"fecha": ayer, "numero": 42}))

    # --- S5: contador de cache perdido ---------------------------------------

    def test_s5_contador_borrado_no_produce_colision(self):
        """Modo de falla real: Redis reiniciado a mitad de jornada."""
        for _ in range(3):
            turnos.emitir_turno()

        frappe.cache().delete(turnos._clave_contador(self.fecha))

        emitido = turnos.emitir_turno()

        self.assertEqual(emitido["numero"], 4)
        self.assertEqual(self._conteo_del_dia(), 4)

    def test_s5_contador_desalineado_por_debajo_converge(self):
        """Aunque el contador quede atrasado, la base rechaza y el reintento corrige."""
        for _ in range(5):
            turnos.emitir_turno()

        frappe.cache().set(turnos._clave_contador(self.fecha), 2)

        emitido = turnos.emitir_turno()

        self.assertGreater(emitido["numero"], 5)
        self.assertEqual(self._conteo_del_dia(), 6)

    # --- S3: el invariante crítico -------------------------------------------

    def test_s3_emision_concurrente_no_duplica_numeros(self):
        """Varios clientes tocando el kiosco a la vez deben recibir números distintos."""
        sitio = frappe.local.site
        hilos_count = 8
        resultados: list = [None] * hilos_count
        errores: list = [None] * hilos_count

        def _emitir(indice):
            frappe.init(site=sitio)
            frappe.connect()
            try:
                resultados[indice] = turnos.emitir_turno()["numero"]
                frappe.db.commit()
            except Exception as exc:  # se reporta en el hilo principal
                errores[indice] = exc
            finally:
                frappe.destroy()

        hilos = [threading.Thread(target=_emitir, args=(i,)) for i in range(hilos_count)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()

        fallidos = [e for e in errores if e is not None]
        self.assertEqual(fallidos, [], f"Hilos con error: {fallidos}")

        self.assertEqual(
            len(set(resultados)),
            hilos_count,
            f"Números repetidos entre hilos: {sorted(resultados)}",
        )
        self.assertEqual(self._conteo_del_dia(), hilos_count)

    # --- helpers --------------------------------------------------------------

    def _conteo_del_dia(self):
        return frappe.db.count(DOCTYPE, {"fecha": self.fecha})


class TestAvanceDeLaCola(FrappeTestCase):
    """R2: llamar al siguiente y cerrar el anterior de forma implícita."""

    def setUp(self):
        self.fecha = today()
        _limpiar_turnos(self.fecha)

    def tearDown(self):
        _limpiar_turnos(self.fecha)

    def _estado(self, numero):
        return frappe.db.get_value(DOCTYPE, {"fecha": self.fecha, "numero": numero}, "estado")

    def _en_llamado(self):
        return frappe.get_all(
            DOCTYPE, filters={"fecha": self.fecha, "estado": "Llamado"}, pluck="numero"
        )

    # --- S6: llamar al siguiente ---------------------------------------------

    def test_s6_llama_al_menor_numero_esperando(self):
        _sembrar(self.fecha, 3)
        _sembrar(self.fecha, 4)

        resultado = turnos.llamar_siguiente()

        self.assertEqual(resultado["numero"], 3)
        self.assertEqual(self._estado(3), "Llamado")

    def test_s6_registra_quien_llamo_y_cuando(self):
        _sembrar(self.fecha, 3)

        turnos.llamar_siguiente()

        fila = frappe.db.get_value(
            DOCTYPE,
            {"fecha": self.fecha, "numero": 3},
            ["llamado_en", "llamado_por"],
            as_dict=True,
        )
        self.assertIsNotNone(fila.llamado_en)
        self.assertEqual(fila.llamado_por, frappe.session.user)

    def test_s6_no_toma_turnos_ya_cerrados(self):
        """Un turno atendido o ausente no vuelve a la cola."""
        _sembrar(self.fecha, 1, estado="Atendido")
        _sembrar(self.fecha, 2, estado="Ausente")
        _sembrar(self.fecha, 3)

        self.assertEqual(turnos.llamar_siguiente()["numero"], 3)

    # --- S7: cierre implícito -------------------------------------------------

    def test_s7_el_anterior_pasa_a_atendido(self):
        _sembrar(self.fecha, 3, estado="Llamado")
        _sembrar(self.fecha, 4)

        turnos.llamar_siguiente()

        self.assertEqual(self._estado(3), "Atendido")
        self.assertEqual(self._estado(4), "Llamado")

    def test_s7_el_cierre_deja_marca_de_tiempo(self):
        _sembrar(self.fecha, 3, estado="Llamado")
        _sembrar(self.fecha, 4)

        turnos.llamar_siguiente()

        self.assertIsNotNone(
            frappe.db.get_value(DOCTYPE, {"fecha": self.fecha, "numero": 3}, "cerrado_en")
        )

    # --- S8: cola vacía --------------------------------------------------------

    def test_s8_cola_vacia_informa_sin_error(self):
        _sembrar(self.fecha, 9, estado="Llamado")

        resultado = turnos.llamar_siguiente()

        self.assertTrue(resultado["cola_vacia"])

    def test_s8_cola_vacia_no_altera_el_turno_en_atencion(self):
        """Llamar sin nadie esperando no debe cerrar a quien está siendo atendido."""
        _sembrar(self.fecha, 9, estado="Llamado")

        turnos.llamar_siguiente()

        self.assertEqual(self._estado(9), "Llamado")

    # --- S9: cliente ausente ---------------------------------------------------

    def test_s9_marcar_ausente(self):
        _sembrar(self.fecha, 5, estado="Llamado")

        turnos.marcar_ausente()

        self.assertEqual(self._estado(5), "Ausente")
        self.assertEqual(self._en_llamado(), [])

    def test_s9_marcar_ausente_sin_nadie_en_atencion_no_falla(self):
        _sembrar(self.fecha, 5)

        resultado = turnos.marcar_ausente()

        self.assertFalse(resultado["ok"])
        self.assertEqual(self._estado(5), "Esperando")

    # --- Invariante R2: a lo sumo uno en Llamado -------------------------------

    def test_a_lo_sumo_un_turno_en_llamado_tras_varias_llamadas(self):
        for numero in range(1, 6):
            _sembrar(self.fecha, numero)

        for _ in range(4):
            turnos.llamar_siguiente()
            self.assertLessEqual(len(self._en_llamado()), 1)

        self.assertEqual(self._en_llamado(), [4])

    # --- Push a la TV (Socket.IO room website) ---------------------------------

    def _llamadas_pantalla(self, publish):
        return [
            (args, kwargs)
            for args, kwargs in publish.call_args_list
            if args and args[0] == turnos.EVENTO_PANTALLA
        ]

    def test_llamar_publica_evento_en_room_website(self):
        """Guest no escucha room `all`; la TV vive en `website`.

        El push no espera al commit del request (`after_commit=False`):
        la TV aplica el payload en memoria.
        """
        _sembrar(self.fecha, 3)

        with patch.object(frappe, "publish_realtime") as publish:
            turnos.llamar_siguiente()

        pantallas = self._llamadas_pantalla(publish)
        self.assertEqual(len(pantallas), 1)
        args, kwargs = pantallas[0]
        self.assertEqual(args[1]["numero"], 3)
        self.assertEqual(set(args[1].keys()), {"numero", "desde"})
        self.assertEqual(kwargs.get("room"), frappe.realtime.get_website_room())
        self.assertFalse(kwargs.get("after_commit", False))

    def test_ausente_publica_payload_vacio(self):
        _sembrar(self.fecha, 5, estado="Llamado")

        with patch.object(frappe, "publish_realtime") as publish:
            turnos.marcar_ausente()

        pantallas = self._llamadas_pantalla(publish)
        self.assertEqual(len(pantallas), 1)
        args, kwargs = pantallas[0]
        self.assertEqual(args[1], {})
        self.assertEqual(kwargs.get("room"), frappe.realtime.get_website_room())

    def test_cola_vacia_no_publica(self):
        """Sin cambio de estado en pantalla, no hay ruido en el socket."""
        _sembrar(self.fecha, 9, estado="Llamado")

        with patch.object(frappe, "publish_realtime") as publish:
            turnos.llamar_siguiente()

        self.assertEqual(self._llamadas_pantalla(publish), [])
