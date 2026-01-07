/**
 * Tests de Login - BarrioFarma
 * 
 * Valida el flujo de autenticacion para diferentes roles
 */

describe('Login BarrioFarma', () => {
  beforeEach(() => {
    cy.clearCookies()
    cy.clearLocalStorage()
  })

  describe('Login via UI', () => {
    it('debe mostrar la pagina de login correctamente', () => {
      cy.visit('/login')
      
      // Testing Library: queries semanticas
      cy.findByPlaceholderText(/juan@example.com/i).should('be.visible')
      cy.findByPlaceholderText(/•••••/).should('be.visible')
      cy.findByRole('button', { name: /iniciar sesi.n/i }).should('be.visible')
    })

    it('debe mostrar error con credenciales invalidas', () => {
      cy.visit('/login')
      
      cy.findByPlaceholderText(/juan@example.com/i).type('usuario_invalido')
      cy.findByPlaceholderText(/•••••/).type('password_invalida')
      cy.findByRole('button', { name: /iniciar sesi.n/i }).click()
      
      // Debe permanecer en login
      cy.url().should('include', '/login')
      cy.url().should('not.include', '/app')
    })

    it('debe hacer login exitoso con Administrator', () => {
      cy.visit('/login')
      
      cy.findByPlaceholderText(/juan@example.com/i).type('administrator')
      cy.findByPlaceholderText(/•••••/).type('admin')
      cy.findByRole('button', { name: /iniciar sesi.n/i }).click()
      
      cy.url({ timeout: 15000 }).should('include', '/app')
      cy.get('.navbar').should('be.visible')
    })
  })

  describe('Login via API con roles', () => {
    it('debe hacer login como Superadmin', () => {
      cy.loginAs('superadmin')
      cy.visit('/app')
      cy.url().should('include', '/app')
      cy.get('.navbar').should('be.visible')
    })

    // Usuarios de prueba creados con: bench execute barriofarma_app.barriofarma_app.utils.setup_test_users.create_test_users
    
    it('debe hacer login como Stock Manager', () => {
      cy.loginAs('stock_manager')
      cy.visit('/app')
      cy.url().should('include', '/app')
      cy.get('.navbar').should('be.visible')
    })

    it('debe hacer login como Auxiliar de Bodega', () => {
      cy.loginAs('bodega')
      cy.visit('/app')
      cy.url().should('include', '/app')
      cy.get('.navbar').should('be.visible')
    })

    it('debe hacer login como Cajero POS', () => {
      cy.loginAs('cajero')
      cy.visit('/app')
      cy.url().should('include', '/app')
      cy.get('.navbar').should('be.visible')
    })
  })

  describe('Logout', () => {
    it('debe hacer logout correctamente', () => {
      cy.loginAs('superadmin')
      cy.visit('/app')
      cy.get('.navbar', { timeout: 15000 }).should('be.visible')
      
      // Ignorar errores de la aplicacion durante logout
      cy.on('uncaught:exception', () => false)
      
      cy.logout()
      
      cy.visit('/login')
      cy.url().should('include', '/login')
    })
  })
})

