# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
API de turnos de atención en el local físico.

Issue whiteboard #90 - change SDD barriofarma-turnos-atencion
Spec: barriofarma-turnos-atencion

Numeración: Redis acelera, la base garantiza
--------------------------------------------
El invariante del agregado es que dos clientes nunca reciban el mismo número.
Un `SELECT MAX(numero) + 1` tiene esa carrera de forma estructural, así que la
unicidad la impone la clave primaria del DocType (`format:TRN-{fecha}-{numero}`)
y Redis solo aporta el camino rápido.

Redis es volátil: si se reinicia a mitad de jornada, la clave del día
desaparece y el siguiente `incr` devuelve 1, colisionando con turnos ya
emitidos. Por eso un 1 se trata como ambiguo y se contrasta con la base.

Restricción medida en el bench, no obvia al leer la API de Frappe:
`frappe.cache()` es un `RedisWrapper(redis.Redis)`, así que hereda `incr`, pero
`set_value` / `get_value` serializan con pickle y un `incr` posterior sobre esa
clave lanza `ResponseError`. Sobre el contador solo se usan `set`, `incr` y
`expire` crudos. Además los métodos heredados de redis-py no aplican el prefijo
de sitio, así que `make_key` se invoca a mano o la clave se compartiría entre
sitios del mismo Redis.
"""

from __future__ import annotations

import time

import frappe
from frappe import _

DOCTYPE = "Turno Atencion"

# Evento Socket.IO para la TV de sala. Room `website`: Guest y Website User la
# reciben; room `all` (default de publish_realtime) solo llega a System User.
EVENTO_PANTALLA = "turno_atencion_update"

# Cache de la TV. `set_value` (pickle), no `incr`: ver nota de Redis arriba.
CLAVE_PANTALLA = "turno_atencion:pantalla"

# Long-poll same-origin. El SDK React, si la pagina va con puerto (:8001),
# reescribe el socket a socketio_port (9001). Ese puerto no esta publicado
# al browser del host; Engine.IO espera 20 s y la TV nunca ve el evento.
# 55 s: bajo el corte tipico de proxy a 60 s. El clic del POS despierta antes.
ESPERA_PANTALLA_S = 55
ESPERA_PANTALLA_PASO_S = 0.1

# Sobrevive la jornada con holgura sin dejar claves huérfanas indefinidas.
CONTADOR_TTL = 60 * 60 * 48

# Cada colisión realinea el contador con la base, así que la convergencia es
# rápida. Cinco intentos cubren un pico de concurrencia muy por encima del que
# puede producir una fila física en un mostrador.
MAX_INTENTOS = 5


def _clave_contador(fecha: str) -> str:
	return frappe.cache().make_key(f"turno_atencion:{fecha}")


def _maximo_del_dia(fecha: str) -> int | None:
	"""Mayor número emitido en la fecha, o None si aún no hay turnos.

	Se ordena en vez de agregar: `frappe.db` rechaza funciones SQL como string
	en el SELECT, y el índice sobre `numero` hace que el orden descendente sea
	equivalente en costo a un MAX.
	"""
	maximo = frappe.db.get_value(
		DOCTYPE, {"fecha": fecha}, "numero", order_by="numero desc"
	)
	return int(maximo) if maximo else None


def _siguiente_numero(fecha: str) -> int:
	"""Reserva el siguiente número del día de forma atómica.

	Un `incr` que devuelve 1 es ambiguo: puede ser el primer turno real del día
	o un Redis recién reiniciado. Solo en ese caso se paga la consulta a la base.
	"""
	cache = frappe.cache()
	clave = _clave_contador(fecha)
	numero = cache.incr(clave)

	if numero == 1:
		maximo = _maximo_del_dia(fecha)
		if maximo:
			numero = maximo + 1
			cache.set(clave, numero)

	cache.expire(clave, CONTADOR_TTL)
	return numero


def _resembrar(fecha: str) -> None:
	"""Realinea el contador con la base tras una colisión."""
	cache = frappe.cache()
	cache.set(_clave_contador(fecha), _maximo_del_dia(fecha) or 0)
	cache.expire(_clave_contador(fecha), CONTADOR_TTL)


@frappe.whitelist()
def emitir_turno() -> dict:
	"""Emite el siguiente turno del día. No recibe ni registra dato del cliente.

	El reintento se apoya en un savepoint y no en un rollback completo: una
	colisión es un evento esperado bajo concurrencia, no un fallo de la
	transacción, y no debe descartar trabajo previo del llamador.
	"""
	fecha = frappe.utils.today()

	for intento in range(MAX_INTENTOS):
		punto = f"emitir_turno_{intento}"
		frappe.db.savepoint(punto)
		try:
			turno = frappe.get_doc(
				{"doctype": DOCTYPE, "fecha": fecha, "numero": _siguiente_numero(fecha)}
			).insert()
			return {"numero": turno.numero, "fecha": turno.fecha}
		except frappe.DuplicateEntryError:
			frappe.db.rollback(save_point=punto)
			_resembrar(fecha)

	frappe.throw(
		_("No fue posible emitir el turno. Intente nuevamente."),
		title=_("Turno no emitido"),
	)


# ---------------------------------------------------------------------------
# Avance de la cola
# ---------------------------------------------------------------------------
#
# Write se exige una vez por operación (`_exigir_write`). Las mutaciones van
# por `db.set_value`: `Document.save()` arrastra validate, notify y
# `doc_update`, y con `after_commit` la TV no pintaba hasta terminar el
# request del POS. El kiosco sigue fuera: tiene create, no write.


def _exigir_write() -> None:
	frappe.has_permission(DOCTYPE, "write", throw=True)


def _nombre_en_atencion(fecha: str) -> str | None:
	return frappe.db.get_value(DOCTYPE, {"fecha": fecha, "estado": "Llamado"}, "name")


def _cerrar(nombre: str, estado: str) -> None:
	frappe.db.set_value(
		DOCTYPE,
		nombre,
		{"estado": estado, "cerrado_en": frappe.utils.now_datetime()},
	)


@frappe.whitelist()
def llamar_siguiente() -> dict:
	"""Cierra al que estaba en atención y llama al siguiente en espera.

	El cierre es implícito por decisión de dominio: pedirle al cajero un clic
	extra para cerrar no aporta información de negocio que no se deduzca de
	haber llamado al siguiente.
	"""
	_exigir_write()
	fecha = frappe.utils.today()

	siguiente = frappe.db.get_value(
		DOCTYPE,
		{"fecha": fecha, "estado": "Esperando"},
		["name", "numero"],
		order_by="numero asc",
		as_dict=True,
	)

	if not siguiente:
		return {"cola_vacia": True, "en_atencion": _numero_en_atencion(fecha)}

	anterior = _nombre_en_atencion(fecha)
	if anterior:
		_cerrar(anterior, "Atendido")

	ahora = frappe.utils.now_datetime()
	frappe.db.set_value(
		DOCTYPE,
		siguiente.name,
		{
			"estado": "Llamado",
			"llamado_en": ahora,
			"llamado_por": frappe.session.user,
		},
	)
	_publicar_pantalla({"numero": siguiente.numero, "desde": ahora})

	return {"cola_vacia": False, "numero": siguiente.numero}


@frappe.whitelist()
def marcar_ausente() -> dict:
	"""Cierra como ausente al turno en atención que no se presentó."""
	_exigir_write()
	fecha = frappe.utils.today()

	fila = frappe.db.get_value(
		DOCTYPE,
		{"fecha": fecha, "estado": "Llamado"},
		["name", "numero"],
		as_dict=True,
	)
	if not fila:
		return {"ok": False}

	_cerrar(fila.name, "Ausente")
	_publicar_pantalla({})

	return {"ok": True, "numero": fila.numero}


def _numero_en_atencion(fecha: str) -> int | None:
	return frappe.db.get_value(DOCTYPE, {"fecha": fecha, "estado": "Llamado"}, "numero")


# ---------------------------------------------------------------------------
# Pantalla de sala
# ---------------------------------------------------------------------------


def _payload_pantalla() -> dict:
	"""Misma superficie que el endpoint público (S11): solo numero y desde."""
	fila = frappe.db.get_value(
		DOCTYPE,
		{"fecha": frappe.utils.today(), "estado": "Llamado"},
		["numero", "llamado_en"],
		as_dict=True,
	)
	if not fila:
		return {}
	return _serializar_payload({"numero": fila.numero, "desde": fila.llamado_en})


def _serializar_payload(payload: dict) -> dict:
	if not payload or payload.get("numero") is None:
		return {}
	desde = payload.get("desde")
	return {
		"numero": int(payload["numero"]),
		"desde": str(desde) if desde is not None else None,
	}


def _token_pantalla(payload: dict) -> str:
	if not payload:
		return ""
	return f"{payload.get('numero')}|{payload.get('desde') or ''}"


def _guardar_cache_pantalla(payload: dict) -> None:
	frappe.cache().set_value(CLAVE_PANTALLA, payload, expires_in_sec=60 * 60 * 24)


def _leer_cache_pantalla() -> dict:
	# use_local_cache=False: el loop vive en el request de la TV; si lee
	# frappe.local.cache nunca vera el set_value del POS en otro worker.
	cached = frappe.cache().get_value(CLAVE_PANTALLA, use_local_cache=False)
	if cached is not None:
		return cached if isinstance(cached, dict) else {}
	payload = _payload_pantalla()
	_guardar_cache_pantalla(payload)
	return payload


def _publicar_pantalla(payload: dict) -> None:
	"""Despierta la TV por Redis (long-poll) y, si el socket llega, por Socket.IO.

	`after_commit=False`: la TV no relee la transacción del POS.
	"""
	serializado = _serializar_payload(payload)
	_guardar_cache_pantalla(serializado)
	frappe.publish_realtime(
		EVENTO_PANTALLA,
		serializado,
		room=frappe.realtime.get_website_room(),
		after_commit=False,
	)


@frappe.whitelist(allow_guest=True)
def turno_en_atencion() -> dict:
	"""Número que se está atendiendo. Carga inicial de la TV.

	La respuesta se arma campo por campo a propósito. Devolver el documento con
	`as_dict()` expondría sin autenticación el operador que llamó, el nombre del
	registro y cualquier campo que se agregue después. El escenario S11 compara
	el conjunto exacto de claves para que ese descuido no pase silencioso.

	Sin `@rate_limit`: la clave por defecto es la IP y todos los clientes del
	local salen por la misma, así que estrangularía al monitor legítimo. Es una
	lectura sin efecto de escritura.
	"""
	payload = _payload_pantalla()
	_guardar_cache_pantalla(payload)
	return payload


@frappe.whitelist(allow_guest=True)
def esperar_turno_en_atencion(visto: str | None = None) -> dict:
	"""Long-poll same-origin: vuelve cuando el turno cambia o a los 55 s.

	No usa el puerto socketio. Un GET en vuelo por TV; al llamar el cajero
	el cache Redis cambia y esta request retorna en el siguiente paso (0.1 s).
	Misma superficie que `turno_en_atencion` (S11).
	"""
	visto = visto or ""
	limite = time.monotonic() + ESPERA_PANTALLA_S
	while True:
		payload = _leer_cache_pantalla()
		if _token_pantalla(payload) != visto:
			return payload
		if time.monotonic() >= limite:
			return payload
		time.sleep(ESPERA_PANTALLA_PASO_S)
