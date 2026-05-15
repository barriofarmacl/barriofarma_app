import { describe, expect, it } from 'vitest'
import {
  normalizeLoginUsername,
  validateLoginEmail,
  validateLoginPassword,
} from './login-validation'

describe('normalizeLoginUsername', () => {
  it('recorta espacios', () => {
    expect(normalizeLoginUsername('  a@b.co  ')).toBe('a@b.co')
  })
})

describe('validateLoginEmail', () => {
  it('rechaza vacio', () => {
    expect(validateLoginEmail('')).toMatch(/obligatorio/)
    expect(validateLoginEmail('   ')).toMatch(/obligatorio/)
  })

  it('rechaza formato invalido', () => {
    expect(validateLoginEmail('no-es-correo')).toMatch(/valido/)
  })

  it('acepta correo valido', () => {
    expect(validateLoginEmail('user@barriofarma.cl')).toBeNull()
  })
})

describe('validateLoginPassword', () => {
  it('rechaza vacia', () => {
    expect(validateLoginPassword('')).toMatch(/obligatoria/)
  })

  it('rechaza corta', () => {
    expect(validateLoginPassword('12345')).toMatch(/6 caracteres/)
  })

  it('acepta longitud minima', () => {
    expect(validateLoginPassword('123456')).toBeNull()
  })
})
