import { describe, expect, it } from 'vitest'
import { getCatalogoErrorMessage, parseFrappeServerMessages } from './frappe-errors'

describe('parseFrappeServerMessages', () => {
  it('extrae mensaje del primer server message', () => {
    const raw = JSON.stringify([JSON.stringify({ message: 'Cliente obligatorio' })])
    expect(parseFrappeServerMessages(raw)).toBe('Cliente obligatorio')
  })
})

describe('getCatalogoErrorMessage', () => {
  it('prioriza Error.message', () => {
    expect(getCatalogoErrorMessage(new Error('Fallo de red'), 'fallback')).toBe('Fallo de red')
  })

  it('usa _server_messages cuando existe', () => {
    const raw = JSON.stringify([JSON.stringify({ message: 'Permiso denegado' })])
    expect(
      getCatalogoErrorMessage({ _server_messages: raw }, 'No se pudo crear la orden')
    ).toBe('Permiso denegado')
  })

  it('retorna fallback si no hay detalle', () => {
    expect(getCatalogoErrorMessage({}, 'No se pudo crear la orden')).toBe('No se pudo crear la orden')
  })
})
