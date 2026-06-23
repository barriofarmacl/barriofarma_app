# -*- coding: utf-8 -*-
"""Shims for Frappe API moves between v15 (boot) and v16 (desk_views)."""


def get_allowed_report_names():
	"""Report names visible to the current session user."""
	try:
		from frappe.boot import get_allowed_report_names as boot_fn

		return boot_fn()
	except ImportError:
		from frappe.desk.desk_views import DeskViews

		return DeskViews.get_allowed_report_names()


def get_workspace_sidebar_items():
	"""Workspace pages permitted for the current user (desk sidebar source)."""
	try:
		from frappe.desk.desktop import get_workspace_sidebar_items as desktop_fn

		return desktop_fn()
	except ImportError:
		from frappe.desk.desktop import get_workspaces

		return get_workspaces()


def get_sidebar_items_for_user():
	"""Sidebar link groups keyed by workspace/module label (lowercase)."""
	from frappe.boot import get_sidebar_items

	ws = get_workspace_sidebar_items()
	pages = ws.get("pages") or []
	names = []
	for page in pages:
		if isinstance(page, dict):
			name = page.get("name")
		else:
			name = getattr(page, "name", None)
		if name:
			names.append(name)
	return get_sidebar_items(names)
