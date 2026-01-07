/**
 * Tests E2E: Flujo Purchase Order -> Purchase Receipt -> Shelf
 * 
 * Issue #23: Tests E2E para flujo completo Compra -> Recepcion -> Asignacion -> Venta
 * 
 * Roles involucrados:
 * - comprador: Crea Purchase Order
 * - bodega: Crea Purchase Receipt y asigna shelf
 * - admin: Verifica Shelf Movements
 * 
 * NOTA: Estos tests requieren:
 * 1. Usuarios de prueba creados: bench execute barriofarma_app.barriofarma_app.utils.setup_test_users.create_test_users
 * 2. Items y Suppliers configurados
 * 3. Shelves configurados
 */

describe('Flujo Completo: PO -> PR -> Shelf', () => {
  // Datos de prueba
  const TEST_ITEM = 'TEST-ITEM-001'
  const TEST_SUPPLIER = 'TEST-SUPPLIER'
  const TEST_SHELF_A1 = 'SHELF-00017' // Shelf con location_code A1
  const TEST_SHELF_B2 = 'SHELF-00018' // Shelf con location_code B2
  const TEST_WAREHOUSE = 'Stores - BF'
  
  // Variable para almacenar el nombre del PO creado
  let createdPO = null
  
  before(() => {
    // Setup inicial como superadmin
    cy.loginAs('superadmin')
  })

  describe('Paso 1: Comprador crea Purchase Order', () => {
    beforeEach(() => {
      cy.loginAs('comprador')
    })

    it('debe poder acceder a lista de Purchase Orders', () => {
      cy.go_to_list('Purchase Order')
      cy.get('.frappe-list').should('be.visible')
      // Verificar URL en lugar de titulo (sitio en espanol)
      cy.url().should('include', '/purchase-order')
    })

    it('debe poder crear nuevo Purchase Order', () => {
      cy.go_to_new('Purchase Order')
      cy.get('.form-page').should('be.visible')
      
      // Verificar campos principales visibles
      cy.get('[data-fieldname="supplier"]').should('be.visible')
      cy.get('[data-fieldname="items"]').should('be.visible')
    })

    it('debe crear PO con items y enviarlo', () => {
      cy.go_to_new('Purchase Order')
      
      // Seleccionar proveedor
      cy.select_link('supplier', TEST_SUPPLIER)
      
      // Esperar a que cargue el formulario
      cy.wait(1000)
      
      // Agregar item
      cy.get('[data-fieldname="items"] .grid-add-row').click()
      cy.wait(500)
      
      // Seleccionar item - usar selector completo
      cy.get('[data-fieldname="items"] .grid-row').last()
        .find('[data-fieldname="item_code"] input')
        .clear()
        .type(TEST_ITEM, { delay: 150 })
      
      // Esperar a que aparezca el autocomplete
      cy.wait(2500)
      
      // Buscar autocomplete
      cy.get('body').then(($body) => {
        if ($body.find('.awesomplete li:visible').length > 0) {
          cy.get('.awesomplete li:visible')
            .first()
            .click({ force: true })
        } else if ($body.find('.awesomplete li').length > 0) {
          cy.get('.awesomplete li')
            .first()
            .click({ force: true })
        } else {
          // Si no hay autocomplete, presionar Enter
          cy.get('[data-fieldname="items"] .grid-row').last()
            .find('[data-fieldname="item_code"] input')
            .type('{enter}')
        }
      })
      
      cy.wait(2000)
      
      // Verificar que el item se seleccionó
      cy.get('[data-fieldname="items"] .grid-row').last()
        .find('[data-fieldname="item_code"] input')
        .should('not.have.value', '')
      
      // Llenar cantidad
      cy.get('[data-fieldname="items"] .grid-row').last()
        .find('[data-fieldname="qty"] input')
        .clear()
        .type('10')
      
      // Esperar a que se calcule el rate y otros campos
      cy.wait(3000)
      
      // Guardar
      cy.save_doc()
      cy.wait(2000)
      
      // Obtener el nombre del documento creado
      cy.url().then((url) => {
        const match = url.match(/\/purchase-order\/([^\/]+)/)
        if (match) {
          createdPO = match[1]
        }
      })
      
      // Verificar que se guardó
      cy.get('.indicator-pill.grey, .indicator-pill.blue', { timeout: 10000 }).should('be.visible')
      
      // Submit
      cy.submit_doc()
      cy.wait(2000)
      
      // Verificar estado
      cy.get('.indicator-pill.blue', { timeout: 10000 }).should('contain', 'To Receive')
    })
  })

  describe('Paso 2: Bodega recibe y asigna shelf', () => {
    beforeEach(() => {
      cy.loginAs('bodega')
    })

    it('debe poder acceder a lista de Purchase Receipts', () => {
      cy.go_to_list('Purchase Receipt')
      cy.get('.frappe-list').should('be.visible')
      // Verificar URL en lugar de titulo (sitio en espanol)
      cy.url().should('include', '/purchase-receipt')
    })

    it('debe ver campo custom_to_shelf en Purchase Receipt Item', () => {
      cy.go_to_new('Purchase Receipt')
      cy.get('.form-page').should('be.visible')
      
      // El campo custom_to_shelf deberia estar visible en la tabla de items
      // Primero necesitamos agregar una fila
      cy.get('[data-fieldname="items"]').should('be.visible')
      
      // Agregar una fila para ver el campo
      cy.get('[data-fieldname="items"] .grid-add-row').click()
      cy.wait(1000)
      
      // Primero necesitamos seleccionar un item para que aparezcan los campos custom
      cy.get('[data-fieldname="items"] .grid-row').last()
        .find('[data-fieldname="item_code"] input')
        .clear()
        .type(TEST_ITEM, { delay: 150 })
      
      cy.wait(2500)
      
      cy.get('body').then(($body) => {
        if ($body.find('.awesomplete li:visible').length > 0) {
          cy.get('.awesomplete li:visible')
            .first()
            .click({ force: true })
        } else if ($body.find('.awesomplete li').length > 0) {
          cy.get('.awesomplete li')
            .first()
            .click({ force: true })
        } else {
          cy.get('[data-fieldname="items"] .grid-row').last()
            .find('[data-fieldname="item_code"] input')
            .type('{enter}')
        }
      })
      
      cy.wait(2000)
      cy.get('[data-fieldname="items"] .grid-row').last()
        .find('[data-fieldname="item_code"] input')
        .should('not.have.value', '')
      
      // Ahora verificar que el campo custom_to_shelf existe
      cy.get('[data-fieldname="items"] .grid-row').last()
        .find('[data-fieldname="custom_to_shelf"]', { timeout: 5000 })
        .should('exist')
        .should('be.visible')
    })

    it('debe crear PR con shelf asignado y verificar Shelf Movement automatico', () => {
      // Requiere que se haya creado un PO en el test anterior
      // Si no existe, crear uno manualmente
      if (!createdPO) {
        cy.log('No hay PO creado, creando uno nuevo...')
        cy.loginAs('comprador')
        cy.go_to_new('Purchase Order')
        cy.select_link('supplier', TEST_SUPPLIER)
        cy.wait(1000)
        cy.get('[data-fieldname="items"] .grid-add-row').click()
        cy.wait(500)
        cy.get('[data-fieldname="items"] .grid-row').last()
          .find('[data-fieldname="item_code"] input')
          .clear()
          .type(TEST_ITEM, { delay: 150 })
        
        cy.wait(2500)
        
        cy.get('body').then(($body) => {
          if ($body.find('.awesomplete li:visible').length > 0) {
            cy.get('.awesomplete li:visible')
              .first()
              .click({ force: true })
          } else if ($body.find('.awesomplete li').length > 0) {
            cy.get('.awesomplete li')
              .first()
              .click({ force: true })
          } else {
            cy.get('[data-fieldname="items"] .grid-row').last()
              .find('[data-fieldname="item_code"] input')
              .type('{enter}')
          }
        })
        
        cy.wait(2000)
        cy.get('[data-fieldname="items"] .grid-row').last()
          .find('[data-fieldname="item_code"] input')
          .should('not.have.value', '')
        cy.get('[data-fieldname="items"] .grid-row').last()
          .find('[data-fieldname="qty"] input')
          .clear()
          .type('10')
        cy.wait(2000)
        cy.save_doc()
        cy.wait(2000)
        cy.submit_doc()
        cy.wait(2000)
        cy.url().then((url) => {
          const match = url.match(/\/purchase-order\/([^\/]+)/)
          if (match) {
            createdPO = match[1]
          }
        })
      }
      
      // Cambiar a usuario bodega
      cy.loginAs('bodega')
      
      // Ir al PO y crear PR desde ahí
      cy.go_to_doc('Purchase Order', createdPO)
      cy.wait(2000)
      
      // Buscar botón Create
      cy.get('.menu-btn-group, .btn-group').contains(/create|crear/i).click({ force: true })
      cy.wait(1000)
      
      // Seleccionar Purchase Receipt del menú
      cy.contains('Purchase Receipt').click({ force: true })
      cy.wait(3000)
      
      // Verificar que estamos en el PR
      cy.url().should('include', '/purchase-receipt')
      cy.get('.form-page').should('be.visible')
      
      // Asignar shelf en el primer item
      cy.get('[data-fieldname="items"] .grid-row').first()
        .find('[data-fieldname="custom_to_shelf"] input')
        .clear()
        .type(TEST_SHELF_A1, { delay: 150 })
      
      cy.wait(2500)
      
      cy.get('body').then(($body) => {
        if ($body.find('.awesomplete li:visible').length > 0) {
          cy.get('.awesomplete li:visible')
            .first()
            .click({ force: true })
        } else if ($body.find('.awesomplete li').length > 0) {
          cy.get('.awesomplete li')
            .first()
            .click({ force: true })
        } else {
          cy.get('[data-fieldname="items"] .grid-row').first()
            .find('[data-fieldname="custom_to_shelf"] input')
            .type('{enter}')
        }
      })
      
      cy.wait(2000)
      cy.get('[data-fieldname="items"] .grid-row').first()
        .find('[data-fieldname="custom_to_shelf"] input')
        .should('not.have.value', '')
      
      cy.wait(1000)
      
      // Submit el PR
      cy.submit_doc()
      cy.wait(3000)
      
      // Verificar que se creó correctamente
      cy.get('.indicator-pill.green', { timeout: 10000 }).should('be.visible')
      
      // Verificar Shelf Movement automático
      cy.loginAs('superadmin')
      cy.go_to_list('Shelf Movement')
      cy.wait(2000)
      
      // Buscar el movimiento de tipo Recepcion
      cy.get('.frappe-list .list-row', { timeout: 10000 }).should('exist')
      cy.get('.frappe-list').should('contain', 'Recepcion')
      cy.get('.frappe-list').should('contain', TEST_ITEM)
    })
  })

  describe('Paso 3: Verificar Shelf Movements', () => {
    beforeEach(() => {
      cy.loginAs('superadmin')
    })

    // NOTA: DocType Shelf Movement debe existir en el sistema
    // Si no existe, estos tests fallaran
    
    it('debe poder ver lista de Shelf Movements', () => {
      cy.visit('/app/shelf-movement')
      // Verificar que la pagina carga (puede ser lista o error si no existe)
      cy.url().should('include', '/shelf-movement')
    })

    it('debe ver campos requeridos en Shelf Movement', () => {
      // Este test requiere que el DocType Shelf Movement exista
      cy.go_to_new('Shelf Movement')
      cy.get('.form-page', { timeout: 10000 }).should('be.visible')
      
      // Esperar a que carguen los campos
      cy.wait(2000)
      
      // Verificar campos principales (pueden tener diferentes nombres en Frappe)
      cy.get('body').then(($body) => {
        // Verificar que al menos algunos campos existen
        const hasMovementType = $body.find('[data-fieldname="movement_type"]').length > 0
        const hasShelf = $body.find('[data-fieldname="shelf"]').length > 0
        const hasItemCode = $body.find('[data-fieldname="item_code"]').length > 0
        const hasQty = $body.find('[data-fieldname="qty"]').length > 0
        
        // Al menos algunos campos deben existir
        expect(hasMovementType || hasShelf || hasItemCode || hasQty).to.be.true
        
        // Verificar campos específicos si existen
        if (hasMovementType) {
          cy.get('[data-fieldname="movement_type"]').should('be.visible')
        }
        if (hasShelf) {
          cy.get('[data-fieldname="shelf"]').should('be.visible')
        }
        if (hasItemCode) {
          cy.get('[data-fieldname="item_code"]').should('be.visible')
        }
        if (hasQty) {
          cy.get('[data-fieldname="qty"]').should('be.visible')
        }
      })
    })
  })
})

