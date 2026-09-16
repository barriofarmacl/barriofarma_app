#!/usr/bin/env bash
# Ensure wkhtmltopdf can resolve the local site hostname (report_to_pdf HostNotFoundError).
# Run inside the bench/devcontainer. Requires write to /etc/hosts (sudo).
set -euo pipefail

HOST_ENTRY="${1:-barriofarma16.localhost}"
if grep -qE "[[:space:]]${HOST_ENTRY}([[:space:]]|$)" /etc/hosts; then
	echo "OK: ${HOST_ENTRY} already in /etc/hosts"
	exit 0
fi

LINE="127.0.0.1 ${HOST_ENTRY}"
if [ "$(id -u)" -eq 0 ]; then
	printf '%s\n' "$LINE" >> /etc/hosts
else
	echo "$LINE" | sudo tee -a /etc/hosts >/dev/null
fi
echo "OK: added ${LINE} to /etc/hosts"
