# -*- coding: utf-8 -*-
"""Marca del tile ERPNext en la pantalla Apps del Desk.

El titulo y el logo salen de add_to_apps_screen en erpnext/hooks.py. Este
boot_session los reemplaza en el payload, sin parchear el core, para que el
proximo pin de ERPNext no los pise.
"""

APPS_SCREEN_APP = "erpnext"
APPS_SCREEN_TITLE = "BarrioFarma"
APPS_SCREEN_LOGO = "/assets/barriofarma_app/images/bf-apps-icon.svg"


def apply_apps_screen_brand(bootinfo):
	"""boot_session: el tile de erpnext muestra la marca BarrioFarma."""
	for app in bootinfo.get("app_data") or []:
		if app.get("app_name") != APPS_SCREEN_APP:
			continue
		app["app_title"] = APPS_SCREEN_TITLE
		app["app_logo_url"] = APPS_SCREEN_LOGO


def apply_public_brand(context):
	"""update_website_context: login y paginas publicas usan el isotipo BF.

	get_app_logo() elige el logo de ERPNext cuando hay exactamente dos
	app_logo_url (Frappe y ERPNext). Este hook corre despues y lo reemplaza.
	"""
	return {
		"logo": APPS_SCREEN_LOGO,
		"favicon": APPS_SCREEN_LOGO,
		"splash_image": APPS_SCREEN_LOGO,
	}
