#!/usr/bin/env bash
# Smoke suite: unit + domain (objetivo PR/CI).
#
# Importante: `bench run-tests --module barriofarma_app...tests.unit` (solo el paquete)
# ejecuta loadTestsFromModule sobre __init__.py y NO descubre test_*.py en submodulos;
# por eso este script itera cada test_*.py y lanza un --module por archivo.
#
# Uso: desde frappe-bench: ./apps/barriofarma_app/scripts/run_smoke_tests.sh [SITE]
set -euo pipefail

SITE="${1:-barriofarma.localhost}"
# bench solo hace sys.exit(!=0) ante fallos de test si CI esta definido (frappe/commands/utils.py).
export CI="${CI:-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# Paquete Python real: apps/barriofarma_app/barriofarma_app/barriofarma_app/
PKG_ROOT="$(cd "$APP_ROOT/barriofarma_app/barriofarma_app" && pwd)"
TESTS_ROOT="$PKG_ROOT/tests"

cd "$BENCH_ROOT"

run_layer() {
	local layer="$1"
	local dir="$TESTS_ROOT/$layer"
	local -a files=()
	local py base mod

	shopt -s nullglob
	files=("$dir"/test_*.py)
	shopt -u nullglob

	if ((${#files[@]} == 0)); then
		echo "run_smoke_tests: no hay test_*.py en $dir" >&2
		exit 1
	fi

	for py in "${files[@]}"; do
		base=$(basename "$py" .py)
		mod="barriofarma_app.barriofarma_app.tests.$layer.$base"
		echo "==> smoke: $mod"
		bench --site "$SITE" run-tests --module "$mod"
	done
}

run_layer unit
run_layer domain

echo "run_smoke_tests: OK (unit + domain)"
