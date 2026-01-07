# Ejecución de Tests UI con Cypress - BarrioFarma

## Métodos de Ejecución

### 1. Método Recomendado: `bench run-ui-tests` (Frappe Framework)

Este es el método oficial recomendado por Frappe Framework. Se ejecuta desde el directorio `frappe-bench`.

#### Ejecución Interactiva (Modo Desarrollo)

**IMPORTANTE:** El modo interactivo requiere un display gráfico. Si estás en un entorno sin display (Docker, WSL sin X11), usa el modo headless.

```bash
cd /workspace/development/frappe-bench
bench --site barriofarma.localhost run-ui-tests barriofarma_app
```

Abre la interfaz gráfica de Cypress donde puedes:
- Ver todos los tests disponibles
- Ejecutar tests individuales
- Ver la ejecución en tiempo real
- Debuggear tests fallidos

**Solución para errores de IPC en modo interactivo:**

Si ves el error "Terminating renderer for bad IPC message", es porque no hay display disponible. 

**Resultados de pruebas realizadas:**

✅ **Opción 1: Modo Headless SIN DISPLAY (RECOMENDADO - FUNCIONA PERFECTAMENTE)**
```bash
# IMPORTANTE: Asegúrate de que DISPLAY NO esté configurado
unset DISPLAY
bench --site barriofarma.localhost run-ui-tests barriofarma_app --headless --browser electron
```
- ✅ **8/8 tests pasando** (verificado)
- ✅ No requiere display
- ✅ Screenshots automáticos en fallos
- ✅ Ideal para CI/CD y desarrollo

❌ **Opción 2: DISPLAY=:0 (NO FUNCIONA)**
```bash
export DISPLAY=:0
bench --site barriofarma.localhost run-ui-tests barriofarma_app
```
- ❌ Error: "Missing X server or $DISPLAY"
- ❌ Requiere servidor X real (no disponible en Docker/WSL sin X11)
- ⚠️ **Nota:** Si DISPLAY está configurado, incluso el modo headless falla

❌ **Opción 3: Xvfb (INICIA PERO FALLA)**
```bash
xvfb-run -a bench --site barriofarma.localhost run-ui-tests barriofarma_app
```
- ⚠️ Inicia Cypress correctamente
- ❌ Error de IPC: "Terminating renderer for bad IPC message, reason 114"
- ❌ Problema conocido con Electron en algunos entornos

**Conclusión:** Usar **modo headless SIN configurar DISPLAY** es la única opción que funciona correctamente.

#### Ejecución Headless (CI/CD y Desarrollo - RECOMENDADO)
```bash
cd /workspace/development/frappe-bench

# IMPORTANTE: Asegúrate de que DISPLAY no esté configurado
unset DISPLAY

# Ejecutar tests
bench --site barriofarma.localhost run-ui-tests barriofarma_app --headless --browser electron
```

**Nota:** Si tienes `DISPLAY` configurado en tu entorno, desconfigúralo antes de ejecutar tests headless:
```bash
unset DISPLAY
```

Ejecuta todos los tests en modo headless (sin interfaz gráfica), ideal para:
- Integración continua (CI/CD)
- Ejecución automatizada
- Validación rápida

#### Ejecución en Paralelo
```bash
bench --site barriofarma.localhost run-ui-tests barriofarma_app --headless --parallel
```

Ejecuta tests en paralelo para reducir tiempo de ejecución.

#### Ejecución con Cobertura
```bash
bench --site barriofarma.localhost run-ui-tests barriofarma_app --headless --with-coverage
```

Genera reporte de cobertura de código.

#### Ejecución en Navegador Específico
```bash
bench --site barriofarma.localhost run-ui-tests barriofarma_app --headless --browser chrome
bench --site barriofarma.localhost run-ui-tests barriofarma_app --headless --browser firefox
bench --site barriofarma.localhost run-ui-tests barriofarma_app --headless --browser edge
```

#### Ejecutar Test Específico
```bash
bench --site barriofarma.localhost run-ui-tests barriofarma_app --headless -- --spec "cypress/integration/02_flujo_po_pr_shelf.cy.js"
```

### 2. Método Alternativo: Scripts NPM (Directo)

Si prefieres ejecutar Cypress directamente desde el directorio de la app:

#### Ejecución Headless (Todos los tests)
```bash
cd /workspace/development/frappe-bench/apps/barriofarma_app
yarn test
# o
npm test
```

#### Ejecución Interactiva
```bash
cd /workspace/development/frappe-bench/apps/barriofarma_app
yarn test:open
# o
npm run test:open
```

#### Ejecución Headless con Interfaz Visual
```bash
cd /workspace/development/frappe-bench/apps/barriofarma_app
yarn test:headed
# o
npm run test:headed
```

### 3. Método Avanzado: Cypress CLI Directo

Para control total sobre la ejecución:

```bash
cd /workspace/development/frappe-bench/apps/barriofarma_app

# Ejecutar todos los tests
npx cypress run --config-file cypress.config.js

# Ejecutar test específico
npx cypress run --config-file cypress.config.js --spec "cypress/integration/01_login.cy.js"

# Ejecutar con variables de entorno
CYPRESS_baseUrl=http://barriofarma.localhost:8000 npx cypress run --config-file cypress.config.js
```

## Pre-requisitos

### 0. Configurar /etc/hosts (IMPORTANTE)

Antes de ejecutar los tests, asegúrate de que `barriofarma.localhost` esté configurado en `/etc/hosts`:

```bash
# Verificar si ya existe
grep "barriofarma.localhost" /etc/hosts

# Si no existe, agregarlo (requiere sudo)
echo "127.0.0.1 barriofarma.localhost" | sudo tee -a /etc/hosts

# Verificar que resuelve correctamente
ping -c 1 barriofarma.localhost
```

**Nota:** Sin esta configuración, Cypress no podrá conectarse al servidor.

### 1. Servidor Frappe en Ejecución

Antes de ejecutar los tests, el servidor Frappe debe estar corriendo:

```bash
cd /workspace/development/frappe-bench
bench start
```

O en modo desarrollo:
```bash
bench --site barriofarma.localhost serve
```

### 2. Datos de Prueba Configurados

Asegúrate de tener los datos de prueba necesarios:

```bash
# Crear usuarios de prueba
bench --site barriofarma.localhost execute \
    barriofarma_app.barriofarma_app.utils.setup_test_users.create_test_users

# Crear datos de prueba (Items, Suppliers, Shelves, etc.)
bench --site barriofarma.localhost execute \
    barriofarma_app.barriofarma_app.utils.setup_ui_test_data.create_ui_test_data
```

### 3. Verificar Estado de Datos

```bash
# Verificar usuarios
bench --site barriofarma.localhost execute \
    barriofarma_app.barriofarma_app.utils.setup_test_users.get_test_users_status

# Verificar datos de prueba
bench --site barriofarma.localhost execute \
    barriofarma_app.barriofarma_app.utils.setup_ui_test_data.get_ui_test_data_status
```

## Estructura de Tests

Los tests están organizados en:

```
cypress/
├── integration/
│   ├── 01_login.cy.js              # Tests de autenticación
│   ├── 02_flujo_po_pr_shelf.cy.js # Flujo PO -> PR -> Shelf
│   ├── 03_pos_shelf.cy.js         # Integración POS-Shelf
│   └── 04_shelf_movement_auto.cy.js # Automatización Shelf Movement
├── support/
│   └── e2e.js                      # Helpers y comandos personalizados
└── config.js                       # Configuración de Cypress
```

## Buenas Prácticas

### 1. Orden de Ejecución

Los tests están numerados para ejecutarse en orden:
- `01_*` - Tests básicos (login, configuración)
- `02_*` - Tests de flujos principales
- `03_*` - Tests de integración
- `04_*` - Tests de automatización

### 2. Aislamiento de Tests

Cada test debe ser independiente:
- Usar `beforeEach()` para setup
- Limpiar datos después de cada test
- No depender de tests anteriores

### 3. Datos de Prueba

- Usar prefijos `TEST-*` para identificar datos de prueba
- Limpiar datos después de ejecutar tests
- No usar datos de producción

### 4. Timeouts

La configuración actual incluye:
- `defaultCommandTimeout: 15000` (15 segundos)
- `pageLoadTimeout: 60000` (60 segundos)
- `requestTimeout: 15000` (15 segundos)

Ajustar según necesidad de la aplicación.

### 5. Screenshots y Videos

- Screenshots automáticos en fallos: `screenshotOnRunFailure: true`
- Videos deshabilitados por defecto: `video: false`
- Habilitar videos solo para debugging

## Troubleshooting

### Error: "Cannot connect to baseUrl"

Verificar que el servidor Frappe está corriendo:
```bash
bench start
```

### Error: "Terminating renderer for bad IPC message" (Modo Interactivo)

Este error ocurre cuando Cypress/Electron no puede renderizar en modo interactivo, común en:
- Entornos Docker sin display
- WSL sin X11 configurado
- SSH sin X11 forwarding

**Solución recomendada: Usar modo headless con debugging**

En lugar de modo interactivo, usa headless con screenshots y logs:

```bash
# Headless con screenshots automáticos en fallos
bench --site barriofarma.localhost run-ui-tests barriofarma_app \
    --headless --browser electron

# Ver screenshots después de fallos
ls -la cypress/screenshots/
```

**Alternativas si necesitas modo interactivo:**

1. **Usar modo headless (recomendado):**
   ```bash
   bench --site barriofarma.localhost run-ui-tests barriofarma_app --headless --browser electron
   ```

2. **Configurar display (si estás en WSL/SSH):**
   ```bash
   export DISPLAY=:0
   # o para X11 forwarding desde Windows:
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
   ```

3. **Usar Xvfb para display virtual:**
   ```bash
   sudo apt-get install xvfb
   xvfb-run -a bench --site barriofarma.localhost run-ui-tests barriofarma_app
   ```

### Error: "User not found"

Crear usuarios de prueba:
```bash
bench --site barriofarma.localhost execute \
    barriofarma_app.barriofarma_app.utils.setup_test_users.create_test_users
```

### Error: "Item not found"

Crear datos de prueba:
```bash
bench --site barriofarma.localhost execute \
    barriofarma_app.barriofarma_app.utils.setup_ui_test_data.create_ui_test_data
```

### Error: "Autocomplete no aparece en tests"

Este es un problema conocido en tests E2E de Frappe. El autocomplete puede no aparecer en modo headless. Soluciones:

1. **Aumentar timeouts:**
   - Los tests ya incluyen timeouts aumentados (2500ms)
   - Si persiste, aumentar en `cypress.config.js`

2. **Ejecutar en modo interactivo para debugging:**
   ```bash
   # Requiere display configurado
   bench --site barriofarma.localhost run-ui-tests barriofarma_app
   ```

3. **Usar API de Frappe para crear datos base:**
   - Crear documentos via API antes de validar en UI
   - Esto reduce la dependencia del autocomplete

### Tests muy lentos

- Reducir timeouts si es posible
- Ejecutar en paralelo: `--parallel`
- Ejecutar solo tests específicos: `--spec`

## Integración Continua (CI/CD)

Para CI/CD, usar:

```bash
bench --site barriofarma.localhost run-ui-tests barriofarma_app \
    --headless \
    --parallel \
    --browser chrome
```

Esto ejecuta todos los tests en modo headless, en paralelo, usando Chrome.

## Scripts de Ayuda

### Script de Debug

Para ejecutar tests con más información y debugging:

```bash
# Todos los tests
./cypress/scripts/debug-test.sh barriofarma.localhost

# Test específico
./cypress/scripts/debug-test.sh barriofarma.localhost "cypress/integration/02_flujo_po_pr_shelf.cy.js"
```

## Problemas Conocidos

### Autocomplete en Campos Link

Los tests que interactúan con campos Link (Item, Supplier, Shelf, etc.) pueden fallar porque el autocomplete no aparece en modo headless. Esto es un problema conocido en tests E2E de Frappe.

**Estado actual:**
- 5 de 8 tests pasando (62.5%)
- 3 tests fallando relacionados con autocomplete

**Workaround:**
- Los tests básicos de navegación y estructura pasan correctamente
- Los tests de creación completa requieren ajustes manuales o ejecución interactiva
- Considerar usar API de Frappe para crear datos base y luego validar en UI

## Referencias

- [Frappe Framework - UI Tests](https://frappeframework.com/docs/user/en/testing/ui-tests)
- [Cypress Documentation](https://docs.cypress.io/)
- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Cypress Troubleshooting](https://docs.cypress.io/guides/references/troubleshooting)

