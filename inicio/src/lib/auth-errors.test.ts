import { describe, expect, it } from 'vitest'
import { getLoginErrorMessage } from './auth-errors'

describe('getLoginErrorMessage', () => {
  it('extrae message string de respuesta Frappe-like', () => {
    expect(getLoginErrorMessage({ message: 'Credenciales incorrectas' })).toBe(
      'Credenciales incorrectas'
    )
  })

  it('extrae primer elemento si message es array', () => {
    expect(getLoginErrorMessage({ message: ['Error A', 'Error B'] })).toBe('Error A')
  })

  it('usa exception si existe', () => {
    expect(getLoginErrorMessage({ exception: 'Traceback...' })).toBe('Traceback...')
  })

  it('usa Error nativo', () => {
    expect(getLoginErrorMessage(new Error('network'))).toBe('network')
  })

  it('fallback generico', () => {
    expect(getLoginErrorMessage(null)).toMatch(/No se pudo iniciar sesion/)
  })
})
