# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Propiedad de precios repartida por tipo de lista.

Issue whiteboard #89 - change SDD barriofarma-tesoreria-precios
Spec: barriofarma-treasury-pricing R1 y R2

Actores de dominio:
- Farmacéutico: comprador y dueño del catálogo. Fija el precio de COMPRA.
- Administrativo: tesorería y control de margen. Fija el precio de VENTA.

`Item Price` es un único DocType para ambos precios: la distinción vive en los
flags `buying` / `selling` de la `Price List`. Los permisos de Frappe operan por
DocType y no por fila, así que la división se impone aquí, sobre el permiso de
DocType que otorga el rol `Purchase Master Manager`.

La lectura queda abierta a ambos perfiles: Administración necesita ver el costo
para calcular margen.
"""

import frappe
from frappe import _

BUYING_OWNER_ROLE = "Farmacéutico"
SELLING_OWNER_ROLE = "Administrativo"
BYPASS_ROLES = frozenset({"System Manager", "Informática", "Administrator"})

FALLBACK_SELLING_PRICE_LIST = "Standard Selling"


def _user_roles(user=None):
	return set(frappe.get_roles(user or frappe.session.user))


def _required_roles(is_buying, is_selling):
	"""Roles exigidos para escribir un precio según el propósito de la lista."""
	required = set()
	if is_buying:
		required.add(BUYING_OWNER_ROLE)
	if is_selling:
		required.add(SELLING_OWNER_ROLE)
	return required


def _is_authorized(roles, is_buying, is_selling):
	"""True si `roles` alcanza para escribir sobre una lista de ese propósito."""
	if set(roles) & BYPASS_ROLES:
		return True
	return _required_roles(is_buying, is_selling).issubset(set(roles))


def _price_list_kind(price_list):
	"""Devuelve (is_buying, is_selling) para la Price List indicada."""
	if not price_list:
		return False, False

	flags = frappe.db.get_value("Price List", price_list, ["buying", "selling"], as_dict=True)
	if not flags:
		return False, False

	return bool(flags.buying), bool(flags.selling)


def _owner_label(is_buying, is_selling):
	owners = []
	if is_buying:
		owners.append(_("Farmacéutico"))
	if is_selling:
		owners.append(_("Administración"))
	return " + ".join(owners)


def _kind_label(is_buying, is_selling):
	kinds = []
	if is_buying:
		kinds.append(_("compra"))
	if is_selling:
		kinds.append(_("venta"))
	return "/".join(kinds)


def validate_item_price_ownership(doc, method=None):
	"""doc_events de Item Price: el precio de compra es del Farmacéutico y el de venta de Administración."""
	is_buying, is_selling = _price_list_kind(doc.get("price_list"))
	if not (is_buying or is_selling):
		return

	roles = _user_roles()
	if _is_authorized(roles, is_buying, is_selling):
		return

	frappe.throw(
		_(
			"La lista <strong>{0}</strong> es de precio de {1}, responsabilidad de "
			"<strong>{2}</strong>. Su perfil puede consultarla pero no modificarla."
		).format(
			doc.get("price_list"),
			_kind_label(is_buying, is_selling),
			_owner_label(is_buying, is_selling),
		),
		title=_("Precio fuera de su responsabilidad"),
	)


def _target_price_lists_on_insert(doc):
	"""Listas que `Item.after_insert` usaría para crear el Item Price inicial.

	Replica `Item.add_price()` de ERPNext, que resuelve a la lista de venta por
	defecto cuando el Item Default no trae una explícita.
	"""
	defaults = doc.get("item_defaults") or []
	price_lists = [d.get("default_price_list") for d in defaults if d.get("default_price_list")]
	if price_lists:
		return price_lists

	fallback = frappe.get_single_value("Selling Settings", "selling_price_list") or frappe.db.get_value(
		"Price List", FALLBACK_SELLING_PRICE_LIST
	)
	return [fallback] if fallback else []


def validate_item_standard_rate_owner(doc, method=None):
	"""doc_events de Item: evita el PermissionError opaco al crear catálogo con precio.

	`Item.after_insert` de ERPNext crea un `Item Price` en la lista de venta cuando
	`standard_rate` viene informado, y ese insert valida permisos. Sin esta guarda el
	Farmacéutico vería un error de permiso críptico y perdería el alta completa.
	"""
	if not doc.is_new() or not doc.get("standard_rate"):
		return

	roles = _user_roles()
	if roles & BYPASS_ROLES:
		return

	for price_list in _target_price_lists_on_insert(doc):
		is_buying, is_selling = _price_list_kind(price_list)
		if not (is_buying or is_selling):
			continue
		if _is_authorized(roles, is_buying, is_selling):
			continue

		frappe.throw(
			_(
				"El precio estándar crearía un precio de {0} en la lista <strong>{1}</strong>, "
				"responsabilidad de <strong>{2}</strong>. Cree el artículo sin precio estándar; "
				"{2} lo cargará después."
			).format(
				_kind_label(is_buying, is_selling),
				price_list,
				_owner_label(is_buying, is_selling),
			),
			title=_("Precio estándar fuera de su responsabilidad"),
		)
