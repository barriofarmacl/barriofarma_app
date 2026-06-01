# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

import frappe
from frappe.desk.doctype.desktop_icon.desktop_icon import DesktopIcon as FrappeDesktopIcon

from barriofarma_app.barriofarma_app.utils.permissions.desktop_icon_policy import (
	FOLDER_LABEL_TO_MODULE,
	get_extra_desktop_icons,
	get_hidden_desktop_icons,
)


class DesktopIcon(FrappeDesktopIcon):
	def _get_icon_module(self):
		if self.icon_type == "Link" and self.link_to:
			if self.link_type == "Workspace Sidebar":
				module = frappe.db.get_value("Workspace Sidebar", self.link_to, "module")
				if module:
					return module
			return frappe.db.get_value("Workspace", self.link_to, "module")

		if self.icon_type == "Folder":
			return FOLDER_LABEL_TO_MODULE.get(self.label)

		return None

	def is_permitted(self, bootinfo):
		label = self.label or self.name
		hidden_icons = get_hidden_desktop_icons()
		if label in hidden_icons:
			return False

		extra_icons = get_extra_desktop_icons()
		if label in extra_icons:
			return self._has_sidebar_content(bootinfo)

		icon_module = self._get_icon_module()
		if icon_module:
			blocked_modules = frappe.get_cached_doc(
				"User", frappe.session.user
			).get_blocked_modules()
			if icon_module in blocked_modules:
				return False

		allowed_roles = [d.role for d in self.get("roles") or []]
		if allowed_roles and not set(allowed_roles).intersection(frappe.get_roles()):
			return False

		if self.icon_type == "Folder":
			return True
		if self.icon_type == "App":
			return self.check_app_permission()

		return self._has_sidebar_content(bootinfo)

	def _has_sidebar_content(self, bootinfo):
		try:
			items = bootinfo.workspace_sidebar_item[self.label.lower()]["items"]
			if len(items) and all(item["type"] == "Section Break" for item in items):
				return False
			if len(items) == 0:
				return False
			return True
		except KeyError:
			return False
