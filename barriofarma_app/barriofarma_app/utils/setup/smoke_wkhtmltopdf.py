# -*- coding: utf-8 -*-
"""DEV smoke: wkhtmltopdf must resolve site host_name (whiteboard #80 follow-up 3)."""

from urllib.parse import urlparse

import frappe
from frappe.utils.pdf import get_pdf


def smoke_report_to_pdf():
	base = (frappe.utils.get_url(allow_header_override=False) or "").rstrip("/")
	html = (
		"<!DOCTYPE html><html><head>"
		f'<link rel="stylesheet" href="{base}/login">'
		"</head><body><p>PDF smoke whiteboard 80</p></body></html>"
	)
	host = urlparse(base).hostname
	pdf = get_pdf(
		html,
		{
			"orientation": "Landscape",
			"proxy": "http://0.0.0.0:0",
			"bypass-proxy-for": host,
			"load-error-handling": "ignore",
		},
	)
	result = {
		"ok": pdf[:4] == b"%PDF",
		"bytes": len(pdf),
		"host": host,
	}
	print(result)
	return result
