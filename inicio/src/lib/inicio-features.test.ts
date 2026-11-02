import { afterEach, describe, expect, it, vi } from 'vitest'
import { isCatalogoTerrenoEnabled } from './inicio-features'

describe('isCatalogoTerrenoEnabled', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    // @ts-expect-error test cleanup
    delete window.frappe
  })

  it('respeta VITE_CATALOGO_TERRENO=0 en build UAT', () => {
    vi.stubEnv('VITE_CATALOGO_TERRENO', '0')
    expect(isCatalogoTerrenoEnabled()).toBe(false)
  })

  it('respeta boot inicio_catalogo_terreno_enabled=0', () => {
    // @ts-expect-error test boot
    window.frappe = { boot: { inicio_catalogo_terreno_enabled: 0 } }
    expect(isCatalogoTerrenoEnabled()).toBe(false)
  })
})
