#!/usr/bin/env bash
# Smoke suite: unit + domain (rapido para PR/CI).
# Uso: desde frappe-bench: ./apps/barriofarma_app/scripts/run_smoke_tests.sh [SITE]
set -euo pipefail
SITE="${1:-barriofarma.localhost}"
BENCH_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$BENCH_ROOT"
bench --site "$SITE" run-tests --module barriofarma_app.barriofarma_app.tests.unit
bench --site "$SITE" run-tests --module barriofarma_app.barriofarma_app.tests.domain
