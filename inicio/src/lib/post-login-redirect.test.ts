import { describe, expect, it } from 'vitest'
import { CATALOGO_PATH, DESK_PATH, TURNO_KIOSCO_PATH, normalizePostLoginPath } from './post-login-redirect'

describe('normalizePostLoginPath', () => {
  it('devuelve catalogo para vendedores terreno', () => {
    expect(normalizePostLoginPath(CATALOGO_PATH)).toBe(CATALOGO_PATH)
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
