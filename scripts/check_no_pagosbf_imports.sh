#!/usr/bin/env bash
# Fail if barriofarma_app Python tree imports pagosbf directly (boundary R4).
# Run from repo root: bash scripts/check_no_pagosbf_imports.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAT='^\s*(from|import)\s+pagosbf\b'
SEARCH="${ROOT}/barriofarma_app"
if [[ ! -d "${SEARCH}" ]]; then
	echo "ERROR: expected Python tree at ${SEARCH}" >&2
	exit 1
fi
if command -v rg >/dev/null 2>&1; then
	if rg --line-number --glob '*.py' "${PAT}" "${SEARCH}"; then
		echo "ERROR: direct imports from pagosbf are forbidden under ${SEARCH}" >&2
		exit 1
	fi
else
	if grep -RIn --include='*.py' -E "${PAT}" "${SEARCH}"; then
		echo "ERROR: direct imports from pagosbf are forbidden under ${SEARCH}" >&2
		exit 1
	fi
fi
echo "OK: no forbidden pagosbf imports under ${SEARCH}"
