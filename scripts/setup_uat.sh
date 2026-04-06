#!/bin/bash
# Script maestro para configuración completa del ambiente UAT
# Barriofarma - Configuración UAT

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
SITE_NAME="${1:-uat.barriofarma.cl}"
SKIP_MIGRATION="${2:-false}"
SKIP_USERS="${3:-false}"
SKIP_DATA="${4:-false}"
SKIP_VALIDATION="${5:-false}"

# Función para imprimir mensajes
print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Verificar que bench está disponible
if ! command -v bench &> /dev/null; then
    print_error "Comando 'bench' no encontrado. Asegúrate de estar en el directorio del bench."
    exit 1
fi

# Verificar que el sitio existe
if ! bench --site "$SITE_NAME" list-apps &> /dev/null; then
    print_error "Sitio '$SITE_NAME' no encontrado o no accesible."
    exit 1
fi

print_header "Configuración UAT - Barriofarma"
echo "Sitio: $SITE_NAME"
echo "Fecha: $(date)"

# Paso 1: Migración
if [ "$SKIP_MIGRATION" != "true" ]; then
    print_header "Paso 1: Ejecutando migración"
    echo "Esto ejecutará automáticamente:"
    echo "  - setup_roles.create_custom_roles()"
    echo "  - setup_permissions.setup_all_permissions()"
    echo ""
    
    if bench --site "$SITE_NAME" migrate; then
        print_success "Migración completada"
    else
        print_error "Error en migración"
        exit 1
    fi
else
    print_warning "Paso 1: Migración omitida (SKIP_MIGRATION=true)"
fi

# Paso 2: Verificar roles (si se omitió la migración)
if [ "$SKIP_MIGRATION" == "true" ]; then
    print_header "Paso 2: Verificando/Creando roles personalizados"
    
    if bench --site "$SITE_NAME" execute \
        barriofarma_app.barriofarma_app.utils.permissions.setup_roles.create_custom_roles; then
        print_success "Roles verificados/creados"
    else
        print_error "Error verificando/creando roles"
        exit 1
    fi
fi

# Paso 3: Configurar permisos (si se omitió la migración)
if [ "$SKIP_MIGRATION" == "true" ]; then
    print_header "Paso 3: Configurando permisos"
    
    if bench --site "$SITE_NAME" execute \
        barriofarma_app.barriofarma_app.utils.permissions.setup_permissions.setup_all_permissions; then
        print_success "Permisos configurados"
    else
        print_error "Error configurando permisos"
        exit 1
    fi
fi

# Paso 4: Crear usuarios UAT
if [ "$SKIP_USERS" != "true" ]; then
    print_header "Paso 4: Creando usuarios UAT"
    
    if bench --site "$SITE_NAME" execute \
        barriofarma_app.barriofarma_app.utils.setup.create_uat_users.create_uat_users; then
        print_success "Usuarios UAT creados"
    else
        print_error "Error creando usuarios UAT"
        exit 1
    fi
else
    print_warning "Paso 4: Creación de usuarios omitida (SKIP_USERS=true)"
fi

# Paso 5: Cargar datos de prueba
if [ "$SKIP_DATA" != "true" ]; then
    print_header "Paso 5: Cargando datos de prueba"
    
    if bench --site "$SITE_NAME" execute \
        barriofarma_app.barriofarma_app.utils.setup.load_uat_data.load_test_data; then
        print_success "Datos de prueba cargados"
    else
        print_error "Error cargando datos de prueba"
        exit 1
    fi
else
    print_warning "Paso 5: Carga de datos omitida (SKIP_DATA=true)"
fi

# Paso 6: Validar configuración
if [ "$SKIP_VALIDATION" != "true" ]; then
    print_header "Paso 6: Validando configuración"
    
    if bench --site "$SITE_NAME" execute \
        barriofarma_app.barriofarma_app.utils.setup.validate_uat_flows.validate_all_flows; then
        print_success "Validación completada"
    else
        print_warning "Validación completada con advertencias (revisar logs)"
    fi
else
    print_warning "Paso 6: Validación omitida (SKIP_VALIDATION=true)"
fi

# Resumen final
print_header "Configuración UAT Completada"
echo ""
echo "Sitio: $SITE_NAME"
echo "Fecha: $(date)"
echo ""
echo "Próximos pasos:"
echo "  1. Verificar que los usuarios pueden iniciar sesión"
echo "  2. Ejecutar pruebas manuales con las guías UAT"
echo "  3. Revisar logs si hay advertencias"
echo ""
print_success "¡Configuración UAT finalizada exitosamente!"
