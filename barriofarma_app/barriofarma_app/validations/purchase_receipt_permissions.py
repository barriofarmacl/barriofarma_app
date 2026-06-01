# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Permisos y reglas de submit para Purchase Receipt (flujo PO -> PR borrador -> QC -> submit).

Actor de dominio:
- Auxiliar: crea PR borrador (recepción física), no submit.
- Farmacéutico: valida QC y submit.
- Bodeguero dedicado: lectura PR; operaciones posteriores vía Stock Entry / Shelf.
"""

import frappe
from frappe import _
from frappe.utils import flt

PR_SUBMIT_ROLES = frozenset({"Farmacéutico", "Informática", "System Manager", "Administrator"})
PR_CREATE_ROLES = frozenset({"Auxiliar", "Bodeguero", "Informática", "System Manager", "Administrator"})


def _user_roles(user=None):
	return set(frappe.get_roles(user or frappe.session.user))


def _is_privileged(roles):
	return bool(roles & PR_SUBMIT_ROLES)


def has_permission(doc, ptype=None, user=None, debug=False):
	"""Hook has_permission para Purchase Receipt (solo puede denegar o permitir continuar)."""
	roles = _user_roles(user)

	if _is_privileged(roles):
		return True

	if ptype == "create":
		if "Farmacéutico" in roles and not (roles & PR_CREATE_ROLES - {"Farmacéutico"}):
			return False
		return True

	if ptype == "submit":
		if "Farmacéutico" in roles:
			return True
		if roles & {"Auxiliar", "Bodeguero"}:
			return False
		return True

	return True


def validate_purchase_receipt_create_authorization(doc):
	"""Solo auxiliar (u operador de bodega dedicado) inicia recepciones."""
	if doc.get("is_return"):
		return

	roles = _user_roles()
	if _is_privileged(roles):
		return

	if "Farmacéutico" in roles and not (roles & PR_CREATE_ROLES - {"Farmacéutico"}):
		frappe.throw(
			_(
				"El <strong>Farmacéutico</strong> no inicia recepciones de compra. "
				"El auxiliar debe crear el Purchase Receipt borrador para revisión y QC."
			),
			title=_("Creación de recepción restringida"),
		)


def validate_purchase_receipt_submit_authorization(doc):
	"""Solo farmacéutico (o roles privilegiados) puede submitir PR."""
	if doc.get("is_return"):
		return

	roles = _user_roles()
	if _is_privileged(roles):
		return

	if "Farmacéutico" not in roles:
		frappe.throw(
			_(
				"Solo un <strong>Farmacéutico</strong> puede validar el control de calidad y "
				"confirmar (Submit) la recepción de compra. El auxiliar debe dejar el documento "
				"en borrador para revisión."
			),
			title=_("Submit de recepción restringido"),
		)


def validate_qc_ready_for_submit(doc):
	"""Toda línea recibida debe tener estado QC explícito antes del submit."""
	if not doc.get("items"):
		return

	for item in doc.items:
		received_qty = flt(item.get("received_qty"))
		if not received_qty:
			continue

		qc_status = (item.get("custom_qc_status") or "").strip()
		if not qc_status:
			frappe.throw(
				_(
					"Fila #{0} ({1}): debe indicar el estado de control de calidad "
					"(custom_qc_status) antes de confirmar la recepción."
				).format(item.idx, frappe.bold(item.item_code)),
				title=_("Control de calidad incompleto"),
			)

		if qc_status in ("Rechazado", "Cuarentena") and not (item.get("custom_qc_rejection_reason") or "").strip():
			frappe.throw(
				_(
					"Fila #{0} ({1}): estado QC <strong>{2}</strong> requiere motivo de rechazo/cuarentena."
				).format(item.idx, frappe.bold(item.item_code), frappe.bold(qc_status)),
				title=_("Motivo QC requerido"),
			)
