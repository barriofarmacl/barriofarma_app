# -*- coding: utf-8 -*-
import frappe
from frappe.desk.doctype.dashboard.dashboard import get_permitted_charts, get_permitted_cards

from barriofarma_app.barriofarma_app.utils.permissions.frappe_v16_compat import (
	get_allowed_report_names,
)

from barriofarma_app.barriofarma_app.utils.permissions.desktop_icon_policy import (
	get_hidden_desktop_icons,
)
from barriofarma_app.barriofarma_app.utils.permissions.setup_admin_accounting_access import (
	get_admin_profile_summary,
)


def check_admin_accounting_access():
	for email in (
		"karla.carmona@barriofarma.cl",
		"jimena.araya@barriofarma.cl",
	):
		summary = get_admin_profile_summary(email)
		if not summary:
			print(email, "SKIP")
			continue
		print("===", email, "===")
		print("Accounts Manager:", summary["has_accounts_manager"])
		print("Accounts module blocked:", summary["accounts_module_blocked"])
		print("Accounting desktop hidden:", "Accounting" in get_hidden_desktop_icons(email))
		for dt, perms in summary["permissions"].items():
			print(f"  {dt}:", perms)

		frappe.set_user(email)
		reports = get_allowed_report_names()
		print(
			"  reports General Ledger:",
			"General Ledger" in reports,
			"Accounts Payable:",
			"Accounts Payable" in reports,
		)
		try:
			charts = get_permitted_charts("Accounts")
			cards = get_permitted_cards("Accounts")
			print("  dashboard Accounts charts=", len(charts), "cards=", len(cards))
		except Exception as exc:
			print("  dashboard Accounts error:", exc)
