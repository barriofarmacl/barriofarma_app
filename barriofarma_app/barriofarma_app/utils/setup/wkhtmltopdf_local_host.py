# -*- coding: utf-8 -*-
# whiteboard #80: Query Report PDF / print. wkhtmltopdf must fetch site assets.
# Site host_name is a FQDN (barriofarma16.localhost). Without /etc/hosts (container
# recreate) Qt fails with HostNotFoundError. Loopback without Host header 404s
# because Frappe routes by Host. Fallback: fetch 127.0.0.1:<port> + Host header.

from __future__ import annotations

import socket
from urllib.parse import urlparse, urlunparse

import frappe


def site_host_resolves(hostname: str) -> bool:
	if not hostname:
		return True
	try:
		socket.getaddrinfo(hostname, None)
		return True
	except OSError:
		return False


def loopback_fetch_target(site_url: str) -> tuple[str, str]:
	parsed = urlparse(site_url)
	port = parsed.port or (443 if parsed.scheme == "https" else 80)
	fetch = urlunparse(parsed._replace(netloc=f"127.0.0.1:{port}"))
	return fetch.rstrip("/"), parsed.netloc


def apply_local_host_fallback(
	html: str,
	options: dict | None,
	*,
	site_url: str,
	host_resolves: bool,
) -> tuple[str, dict]:
	options = dict(options or {})
	if host_resolves or not site_url:
		return html, options
	fetch_url, host_header = loopback_fetch_target(site_url)
	if fetch_url == site_url.rstrip("/"):
		return html, options
	html = html.replace(site_url.rstrip("/"), fetch_url)
	headers = list(options.get("custom-header") or [])
	headers.append(("Host", host_header))
	options["custom-header"] = headers
	options["custom-header-propagation"] = ""
	return html, options


def _rewrite_pdfkit_input(html: str, options: dict | None) -> tuple[str, dict]:
	site_url = (frappe.utils.get_url(allow_header_override=False) or "").rstrip("/")
	hostname = urlparse(site_url).hostname
	return apply_local_host_fallback(
		html,
		options,
		site_url=site_url,
		host_resolves=site_host_resolves(hostname or ""),
	)


def patch_pdfkit_from_string() -> None:
	import pdfkit

	if getattr(pdfkit.from_string, "_barriofarma_wkhtml_host", False):
		return

	original = pdfkit.from_string

	def wrapped(input, output_path=None, options=None, **kwargs):
		input, options = _rewrite_pdfkit_input(input, options)
		return original(input, output_path=output_path, options=options, **kwargs)

	wrapped._barriofarma_wkhtml_host = True
	pdfkit.from_string = wrapped
