import { afterEach, describe, expect, it, vi } from 'vitest'
import { CATALOGO_PATH, DESK_PATH, TURNO_KIOSCO_PATH, normalizePostLoginPath } from './post-login-redirect'

afterEach(() => {
  vi.unstubAllEnvs()
  // @ts-expect-error test cleanup
  delete window.frappe
})

describe('normalizePostLoginPath', () => {
  it('devuelve catalogo para vendedores terreno', () => {
    // @ts-expect-error test boot
    window.frappe = { boot: { inicio_catalogo_terreno_enabled: 1 } }
    expect(normalizePostLoginPath(CATALOGO_PATH)).toBe(CATALOGO_PATH)
  })

  it('envia a desk si catalogo terreno esta apagado en el sitio', () => {
    vi.stubEnv('VITE_CATALOGO_TERRENO', '0')
    expect(normalizePostLoginPath(CATALOGO_PATH)).toBe(DESK_PATH)
  })

  it('devuelve kiosco de turnos para el usuario de tablet', () => {
    expect(normalizePostLoginPath(TURNO_KIOSCO_PATH)).toBe(TURNO_KIOSCO_PATH)
  })

  it('devuelve desk para cualquier otra ruta o valor desconocido', () => {
    expect(normalizePostLoginPath('/app')).toBe(DESK_PATH)
    expect(normalizePostLoginPath(undefined)).toBe(DESK_PATH)
    expect(normalizePostLoginPath('/inicio')).toBe(DESK_PATH)
    expect(normalizePostLoginPath('/inicio/turno')).toBe(DESK_PATH)
  })
})
