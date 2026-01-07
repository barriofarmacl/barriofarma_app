const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://barriofarma.localhost:8000',
    specPattern: 'cypress/integration/**/*.cy.js',
    supportFile: 'cypress/support/e2e.js',
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 15000,
    requestTimeout: 15000,
    responseTimeout: 30000,
    pageLoadTimeout: 60000,
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/screenshots',
    videosFolder: 'cypress/videos',
    
    // Configuracion para Frappe
    experimentalRunAllSpecs: true,
    
    setupNodeEvents(on, config) {
      // Manejar errores de IPC en Electron
      on('before:browser:launch', (browser = {}, launchOptions) => {
        if (browser.name === 'electron') {
          // Agregar flags para evitar errores de IPC
          launchOptions.args.push('--disable-dev-shm-usage')
          launchOptions.args.push('--disable-gpu')
          launchOptions.args.push('--no-sandbox')
          launchOptions.args.push('--disable-setuid-sandbox')
          // Para modo interactivo, deshabilitar algunas optimizaciones
          if (!process.env.CI) {
            launchOptions.args.push('--disable-web-security')
          }
        }
        return launchOptions
      })
      
      return config
    },
  },
  
  // Variables de entorno para tests
  env: {
    // Credenciales por defecto para tests
    ADMIN_USER: 'administrator',
    ADMIN_PASS: 'admin',
    
    // Usuarios de prueba con roles
    TEST_ADMIN: 'test_admin',
    TEST_STOCK_MANAGER: 'test_stock_manager',
    TEST_BODEGA: 'test_bodega',
    TEST_FARMACEUTICO: 'test_farmaceutico',
    TEST_COMPRADOR: 'test_comprador',
    TEST_VENDEDOR: 'test_vendedor',
    TEST_CAJERO: 'test_cajero',
    TEST_PASSWORD: 'Test@123'
  }
})

