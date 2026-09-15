# -*- coding: utf-8 -*-
# whiteboard #80 follow-up 3: wkhtmltopdf HostNotFoundError when site FQDN is not in /etc/hosts.

import unittest
from urllib.parse import urlparse

from barriofarma_app.barriofarma_app.utils.setup.wkhtmltopdf_local_host import (
	apply_local_host_fallback,
	loopback_fetch_target,
	site_host_resolves,
)


class TestWkhtmltopdfLocalHost(unittest.TestCase):
	def test_loopback_fetch_keeps_port_and_host_header(self):
		fetch, header = loopback_fetch_target("http://barriofarma16.localhost:8001")
		self.assertEqual(fetch, "http://127.0.0.1:8001")
		self.assertEqual(header, "barriofarma16.localhost:8001")

	def test_rewrite_only_when_unresolved(self):
		html = '<link href="http://barriofarma16.localhost:8001/assets/x.css">'
		out, options = apply_local_host_fallback(
			html,
			{},
			site_url="http://barriofarma16.localhost:8001",
			host_resolves=False,
		)
		self.assertIn("http://127.0.0.1:8001/assets/x.css", out)
		self.assertNotIn("barriofarma16.localhost", out)
		self.assertIn(("Host", "barriofarma16.localhost:8001"), options["custom-header"])

	def test_no_rewrite_when_host_resolves(self):
		html = '<link href="http://barriofarma16.localhost:8001/assets/x.css">'
		out, options = apply_local_host_fallback(
			html,
			{"orientation": "Landscape"},
			site_url="http://barriofarma16.localhost:8001",
			host_resolves=True,
		)
		self.assertEqual(out, html)
		self.assertNotIn("custom-header", options)

	def test_localhost_resolves(self):
		self.assertTrue(site_host_resolves("localhost"))

	def test_unknown_fqdn_does_not_resolve(self):
		self.assertFalse(site_host_resolves("no-such-host.invalid"))
		self.assertEqual(urlparse("http://no-such-host.invalid").hostname, "no-such-host.invalid")
