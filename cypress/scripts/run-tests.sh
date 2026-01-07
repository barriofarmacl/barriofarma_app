#!/bin/bash
# Script para ejecutar tests Cypress en modo headless (recomendado)

set -e

SITE=${1:-barriofarma.localhost}
TEST_FILE=${2:-""}

echo "=========================================="
echo "Ejecutando tests Cypress (modo headless)"
echo "=========================================="
echo "Site: $SITE"
echo "Test: ${TEST_FILE:-Todos los tests}"
echo ""

# Asegurar que DISPLAY no esté configurado (importante para headless)
unset DISPLAY

cd /workspace/development/frappe-bench

# Verificar que el servidor está corriendo
if ! curl -s http://${SITE}:8000 > /dev/null 2>&1; then
    echo "ERROR: Servidor no responde en http://${SITE}:8000"
    echo "Inicia el servidor con: bench start"
    exit 1
fi

# Ejecutar tests
if [ -n "$TEST_FILE" ]; then
    bench --site $SITE run-ui-tests barriofarma_app \
        --headless --browser electron \
        -- --spec "$TEST_FILE"
else
    bench --site $SITE run-ui-tests barriofarma_app \
        --headless --browser electron
fi

echo ""
echo "=========================================="
echo "Tests completados"
echo "=========================================="
echo "Screenshots: cypress/screenshots/"
echo ""

