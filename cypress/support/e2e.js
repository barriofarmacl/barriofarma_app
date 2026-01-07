/**
 * Cypress Support File para BarrioFarma
 * 
 * Incluye:
 * - Testing Library para queries semanticas
 * - Helpers de login con roles
 * - Helpers de navegacion Frappe
 */

// Importar Testing Library
import '@testing-library/cypress/add-commands'

// =============================================================================
// COMANDOS DE AUTENTICACION
// =============================================================================

/**
 * Login via API REST (rapido, sin UI)
 * @param {string} user - Username
 * @param {string} password - Password
 */
Cypress.Commands.add('login', (user, password) => {
  cy.request({
    method: 'POST',
    url: '/api/method/login',
    body: {
      usr: user,
      pwd: password
    }
  }).then((response) => {
    expect(response.status).to.eq(200)
  })
})

/**
 * Logout via API
 */
Cypress.Commands.add('logout', () => {
  cy.request({
    method: 'GET',
    url: '/api/method/logout',
    failOnStatusCode: false
  })
  cy.clearCookies()
  cy.clearLocalStorage()
})

/**
 * Login con rol especifico (usuarios de prueba)
 * @param {string} role - Nombre del rol: admin, stock_manager, bodega, farmaceutico, comprador, vendedor, cajero
 */
Cypress.Commands.add('loginAs', (role) => {
  // En Frappe, el nombre de usuario es el email completo
  const testPassword = Cypress.env('TEST_PASSWORD') || 'Test@123'
  
  const users = {
    // Administrador del sistema
    admin: { 
      user: 'test_admin@barriofarma.cl', 
      pass: testPassword,
      description: 'Administrador del sistema'
    },
    // Jefe de inventario
    stock_manager: { 
      user: 'test_stock_manager@barriofarma.cl', 
      pass: testPassword,
      description: 'Jefe de inventario'
    },
    // Auxiliar de bodega
    bodega: { 
      user: 'test_bodega@barriofarma.cl', 
      pass: testPassword,
      description: 'Auxiliar de bodega'
    },
    // Farmaceutico / Quimico
    farmaceutico: { 
      user: 'test_farmaceutico@barriofarma.cl', 
      pass: testPassword,
      description: 'Farmaceutico QC'
    },
    // Comprador
    comprador: { 
      user: 'test_comprador@barriofarma.cl', 
      pass: testPassword,
      description: 'Comprador'
    },
    // Vendedor
    vendedor: { 
      user: 'test_vendedor@barriofarma.cl', 
      pass: testPassword,
      description: 'Vendedor'
    },
    // Cajero POS
    cajero: { 
      user: 'test_cajero@barriofarma.cl', 
      pass: testPassword,
      description: 'Cajero POS'
    },
    // Administrator (superusuario)
    superadmin: {
      user: Cypress.env('ADMIN_USER') || 'administrator',
      pass: Cypress.env('ADMIN_PASS') || 'admin',
      description: 'Superadministrador'
    }
  }
  
  const userData = users[role]
  if (!userData) {
    throw new Error(`Rol desconocido: ${role}. Roles disponibles: ${Object.keys(users).join(', ')}`)
  }
  
  cy.log(`Login como: ${userData.description} (${userData.user})`)
  cy.login(userData.user, userData.pass)
})

/**
 * Login via UI (para tests de flujo de login)
 * @param {string} user - Username
 * @param {string} password - Password
 */
Cypress.Commands.add('loginUI', (user, password) => {
  cy.visit('/login')
  cy.findByPlaceholderText(/juan@example.com/i).clear().type(user)
  cy.findByPlaceholderText(/•••••/).clear().type(password)
  cy.findByRole('button', { name: /iniciar sesi.n/i }).click()
  cy.url({ timeout: 15000 }).should('include', '/app')
})

// =============================================================================
// COMANDOS DE NAVEGACION FRAPPE
// =============================================================================

/**
 * Navegar a lista de DocType
 * @param {string} doctype - Nombre del DocType
 */
Cypress.Commands.add('go_to_list', (doctype) => {
  const slug = doctype.toLowerCase().replace(/ /g, '-')
  cy.visit(`/app/${slug}`)
  cy.get('.frappe-list', { timeout: 15000 }).should('be.visible')
})

/**
 * Navegar a documento especifico
 * @param {string} doctype - Nombre del DocType
 * @param {string} name - Nombre del documento
 */
Cypress.Commands.add('go_to_doc', (doctype, name) => {
  const slug = doctype.toLowerCase().replace(/ /g, '-')
  cy.visit(`/app/${slug}/${encodeURIComponent(name)}`)
  cy.get('.form-page', { timeout: 15000 }).should('be.visible')
})

/**
 * Navegar a nuevo documento
 * @param {string} doctype - Nombre del DocType
 */
Cypress.Commands.add('go_to_new', (doctype) => {
  const slug = doctype.toLowerCase().replace(/ /g, '-')
  cy.visit(`/app/${slug}/new-${slug}-1`)
  cy.get('.form-page', { timeout: 15000 }).should('be.visible')
})

/**
 * Navegar a Point of Sale
 * Nota: ERPNext POS puede tener diferentes clases segun la version
 */
Cypress.Commands.add('go_to_pos', () => {
  cy.visit('/app/point-of-sale')
  // Esperar a que cargue el POS (multiples selectores posibles)
  cy.get('.point-of-sale, .pos-app, [data-page-container="point-of-sale"], .page-container[data-page="point-of-sale"]', { timeout: 30000 }).should('exist')
})

// =============================================================================
// COMANDOS DE FORMULARIOS FRAPPE
// =============================================================================

/**
 * Llenar campo de formulario Frappe
 * @param {string} fieldname - Nombre del campo
 * @param {string} value - Valor a ingresar
 */
Cypress.Commands.add('fill_field', (fieldname, value) => {
  cy.get(`[data-fieldname="${fieldname}"] input, [data-fieldname="${fieldname}"] textarea`)
    .clear()
    .type(value)
})

/**
 * Seleccionar valor en campo Link
 * @param {string} fieldname - Nombre del campo
 * @param {string} value - Valor a seleccionar
 */
Cypress.Commands.add('select_link', (fieldname, value) => {
  const inputSelector = `[data-fieldname="${fieldname}"] input`
  
  // Limpiar el campo primero
  cy.get(inputSelector)
    .clear()
    .should('have.value', '')
  
  // Escribir el valor caracter por caracter para activar el autocomplete
  cy.get(inputSelector)
    .type(value, { delay: 150 })
  
  // Esperar a que aparezca el autocomplete (Frappe puede tardar)
  cy.wait(2000)
  
  // Intentar múltiples estrategias para seleccionar
  cy.get('body').then(($body) => {
    // Estrategia 1: Buscar autocomplete visible
    const autocompleteVisible = $body.find('.awesomplete li:visible').length > 0
    const autocompleteAny = $body.find('.awesomplete li').length > 0
    
    if (autocompleteVisible) {
      // Si hay autocomplete visible, seleccionar la primera opción que contenga el valor
      cy.get('.awesomplete li:visible', { timeout: 3000 })
        .contains(new RegExp(value, 'i'))
        .first()
        .click({ force: true })
    } else if (autocompleteAny) {
      // Si hay autocomplete pero no visible, intentar hacerlo visible y seleccionar
      cy.get('.awesomplete li')
        .first()
        .click({ force: true })
    } else {
      // Estrategia 2: Si no hay autocomplete, usar Enter o Tab
      cy.get(inputSelector).then(($input) => {
        // Verificar si el valor ya está en el campo
        if ($input.val() === value) {
          // Si el valor está completo, presionar Enter
          cy.get(inputSelector).type('{enter}')
          cy.wait(1000)
        } else {
          // Si no, intentar escribir completo y presionar Enter
          cy.get(inputSelector)
            .clear()
            .type(value + '{enter}', { delay: 100 })
          cy.wait(1500)
        }
      })
    }
  })
  
  // Esperar a que se procese la selección
  cy.wait(2000)
  
  // Verificar que el valor se estableció (puede ser el nombre completo, no el código)
  cy.get(inputSelector).should('not.have.value', '')
})

/**
 * Guardar documento
 */
Cypress.Commands.add('save_doc', () => {
  cy.get('.primary-action').contains(/guardar|save/i).click()
  cy.get('.msgprint-dialog', { timeout: 10000 }).should('not.exist')
})

/**
 * Submit documento
 */
Cypress.Commands.add('submit_doc', () => {
  cy.get('.primary-action').contains(/enviar|submit/i).click()
  // Confirmar dialogo si aparece
  cy.get('.modal-dialog').then($modal => {
    if ($modal.find('button:contains("Yes")').length > 0) {
      cy.get('.modal-dialog button').contains(/yes|si/i).click()
    }
  })
  cy.get('.indicator-pill.green', { timeout: 15000 }).should('be.visible')
})

// =============================================================================
// COMANDOS DE VERIFICACION
// =============================================================================

/**
 * Verificar que Shelf Movement fue creado
 * @param {string} movement_type - Tipo de movimiento: Recepcion, Venta, Transferencia
 * @param {string} item_code - Codigo del item
 */
Cypress.Commands.add('verify_shelf_movement', (movement_type, item_code) => {
  cy.go_to_list('Shelf Movement')
  cy.get('.frappe-list .list-row').should('contain', movement_type)
  cy.get('.frappe-list .list-row').should('contain', item_code)
})

/**
 * Verificar stock en shelf
 * @param {string} shelf - Nombre del shelf
 * @param {string} item_code - Codigo del item
 * @param {number} expected_qty - Cantidad esperada
 */
Cypress.Commands.add('verify_shelf_stock', (shelf, item_code, expected_qty) => {
  // Navegar a reporte de Stock Balance con filtro de shelf
  cy.visit(`/app/query-report/Stock%20Balance?shelf=${encodeURIComponent(shelf)}&item_code=${encodeURIComponent(item_code)}`)
  cy.get('.dt-cell', { timeout: 15000 }).contains(expected_qty.toString())
})

/**
 * Verificar mensaje de exito
 * @param {string} message - Mensaje esperado (regex o string)
 */
Cypress.Commands.add('verify_success', (message) => {
  cy.get('.msgprint, .alert-success, .indicator-pill.green')
    .should('be.visible')
    .and('contain', message)
})

/**
 * Verificar mensaje de error
 * @param {string} message - Mensaje esperado (regex o string)
 */
Cypress.Commands.add('verify_error', (message) => {
  cy.get('.msgprint-dialog, .alert-danger, .indicator-pill.red')
    .should('be.visible')
    .and('contain', message)
})

// =============================================================================
// CONFIGURACION GLOBAL
// =============================================================================

// Ignorar errores de audio ALSA en entornos headless
Cypress.on('uncaught:exception', (err, runnable) => {
  // Ignorar errores de ALSA (audio) en Linux headless
  if (err.message.includes('ALSA') || err.message.includes('audio')) {
    return false
  }
  // Ignorar errores de ResizeObserver
  if (err.message.includes('ResizeObserver')) {
    return false
  }
  return true
})

// Limpiar cookies antes de cada test
beforeEach(() => {
  cy.clearCookies()
  cy.clearLocalStorage()
})

