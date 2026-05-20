# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""Helper para persistir Shelf Movement enviado (Frappe 15: submit no acepta ignore_permissions)."""

import frappe


def insert_and_submit_shelf_movement(movement) -> None:
	movement.insert(ignore_permissions=True)
	movement.flags.ignore_permissions = True
	movement.submit()
	frappe.db.commit()
