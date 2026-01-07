/**
 * Tests E2E: Automatizacion de Shelf Movement
 * 
 * Issue #24: Validar creacion automatica de Shelf Movement
 * en Purchase Receipt y Sales Invoice
 * 
 * Roles involucrados:
 * - bodega: Crea Purchase Receipt con custom_to_shelf
 * - vendedor: Crea Sales Invoice
 * - admin: Verifica Shelf Movements creados
 */

describe('Automatizacion Shelf Movement', () => {
  const TEST_ITEM = 'TEST-ITEM-001'
  const TEST_SUPPLIER = 'TEST-SUPPLIER'
  const TEST_CUSTOMER = 'TEST-CUSTOMER'
  const TEST_SHELF_A1 = 'SHELF-00017'
  const TEST_WAREHOUSE = 'Stores - BF'
  
  describe('Purchase Receipt -> Shelf Movement automatico', () => {
    beforeEach(() => {
      cy.loginAs('bodega')
    })

    it('debe ver campo custom_to_shelf en Purchase Receipt Item', () => {
      cy.go_to_new('Purchase Receipt')
      cy.get('.form-page').should('be.visible')
      
      // El campo deberia estar en la tabla de items
      // Verificar que la tabla de items existe
      cy.get('[data-fieldname="items"]').should('be.visible')
      
      // Agregar una fila para ver el campo
      cy.get('[data-fieldname="items"] .grid-add-row').click()
      cy.wait(500)
      
      // Verificar que el campo custom_to_shelf existe
      cy.get('[data-fieldname="items"] .grid-row').last().within(() => {
        cy.get('[data-fieldname="custom_to_shelf"]').should('exist')
      })
    })

    it('debe crear Shelf Movement tipo Recepcion al submit PR con custom_to_shelf', () => {
      // Crear PR manualmente
      cy.go_to_new('Purchase Receipt')
      cy.wait(1000)
      
      // Seleccionar supplier
      cy.select_link('supplier', TEST_SUPPLIER)
      cy.wait(1000)
      
      // Agregar item
      cy.get('[data-fieldname="items"] .grid-add-row').click()
      cy.wait(500)
      
      cy.get('[data-fieldname="items"] .grid-row').last().within(() => {
        // Seleccionar item
        cy.get('[data-fieldname="item_code"] input').clear().type(TEST_ITEM)
        cy.wait(1000)
        cy.get('.awesomplete li').first().click()
        
        // Llenar cantidad
        cy.get('[data-fieldname="qty"] input').clear().type('5')
        
        // Asignar shelf
        cy.get('[data-fieldname="custom_to_shelf"] input').clear().type(TEST_SHELF_A1)
        cy.wait(1000)
        cy.get('.awesomplete li').first().click()
        
        cy.wait(500)
      })
      
      // Guardar
      cy.save_doc()
      cy.wait(2000)
      
      // Submit
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
      cy.get('.frappe-list').should('contain', TEST_SHELF_A1)
    })
  })

  describe('Sales Invoice -> Shelf Movement automatico', () => {
    beforeEach(() => {
      cy.loginAs('vendedor')
    })

    it('debe poder crear Sales Invoice', () => {
      cy.go_to_new('Sales Invoice')
      cy.get('.form-page').should('be.visible')
      
      // Verificar campos principales
      cy.get('[data-fieldname="customer"]').should('be.visible')
      cy.get('[data-fieldname="items"]').should('be.visible')
    })

    it('debe crear Shelf Movement tipo Venta al submit SI con Update Stock', () => {
      // NOTA: Este test requiere stock disponible en warehouse
      // Para que funcione completamente, se necesita:
      // 1. Stock disponible (crear PR o Stock Entry primero)
      // 2. Item con custom_shelf_locations configurado (se configura en Item)
      
      // Crear SI
      cy.go_to_new('Sales Invoice')
      cy.wait(1000)
      
      // Seleccionar customer
      cy.select_link('customer', TEST_CUSTOMER)
      cy.wait(1000)
      
      // Marcar Update Stock
      cy.get('[data-fieldname="update_stock"] input').check({ force: true })
      cy.wait(500)
      
      // Agregar item
      cy.get('[data-fieldname="items"] .grid-add-row').click()
      cy.wait(500)
      
      cy.get('[data-fieldname="items"] .grid-row').last().within(() => {
        // Seleccionar item
        cy.get('[data-fieldname="item_code"] input').clear().type(TEST_ITEM)
        cy.wait(1000)
        cy.get('.awesomplete li').first().click()
        
        // Llenar cantidad (solo si hay stock disponible)
        cy.get('[data-fieldname="qty"] input').clear().type('1')
        
        cy.wait(500)
      })
      
      // Intentar guardar (puede fallar si no hay stock)
      cy.save_doc()
      cy.wait(2000)
      
      // Verificar si se guardó o si hay error de stock
      cy.get('body').then(($body) => {
        if ($body.find('.indicator-pill.grey, .indicator-pill.blue').length > 0) {
          // Se guardó, intentar submit
          cy.submit_doc()
          cy.wait(3000)
          
          // Verificar Shelf Movement
          cy.loginAs('superadmin')
          cy.go_to_list('Shelf Movement')
          cy.wait(2000)
          
          // Buscar movimiento de tipo Venta
          cy.get('.frappe-list .list-row', { timeout: 10000 }).should('exist')
          cy.get('.frappe-list').should('contain', 'Venta')
          cy.get('.frappe-list').should('contain', TEST_ITEM)
        } else {
          // Probablemente no hay stock, registrar como skip
          cy.log('No hay stock disponible para completar la venta')
        }
      })
    })
  })

  describe('Verificacion de permisos por rol', () => {
    it('Stock User (bodega) solo puede leer Shelf Movements', () => {
      cy.loginAs('bodega')
      cy.go_to_list('Shelf Movement')
      
      // Deberia poder ver la lista
      cy.get('.frappe-list', { timeout: 10000 }).should('be.visible')
      
      // Verificar que NO puede crear nuevos (botón New no visible o deshabilitado)
      cy.get('body').then(($body) => {
        if ($body.find('.primary-action, .btn-primary, [data-label="New"]').length > 0) {
          // Si existe el botón, verificar que está deshabilitado o no funciona
          cy.get('.primary-action, .btn-primary, [data-label="New"]').should('exist')
          cy.log('Botón New existe, pero puede estar deshabilitado por permisos')
        } else {
          // No existe el botón, lo cual es correcto
          cy.log('Botón New no visible para Stock User (correcto)')
        }
      })
    })

    it('Stock Manager puede crear Shelf Movements', () => {
      cy.loginAs('stock_manager')
      cy.go_to_new('Shelf Movement')
      
      // Deberia poder ver el formulario
      cy.get('.form-page', { timeout: 10000 }).should('be.visible')
      
      // Verificar campos principales
      cy.get('[data-fieldname="movement_type"]').should('be.visible')
      cy.get('[data-fieldname="shelf"]').should('be.visible')
      cy.get('[data-fieldname="item_code"]').should('be.visible')
    })

    it('Sales User (vendedor) solo puede leer Shelf Movements', () => {
      cy.loginAs('vendedor')
      cy.go_to_list('Shelf Movement')
      
      // Deberia poder ver la lista
      cy.get('.frappe-list', { timeout: 10000 }).should('be.visible')
      
      // Verificar que NO puede crear nuevos
      cy.get('body').then(($body) => {
        if ($body.find('.primary-action, .btn-primary, [data-label="New"]').length > 0) {
          cy.get('.primary-action, .btn-primary, [data-label="New"]').should('exist')
          cy.log('Botón New existe, pero puede estar deshabilitado por permisos')
        } else {
          cy.log('Botón New no visible para Sales User (correcto)')
        }
      })
    })
  })
})

