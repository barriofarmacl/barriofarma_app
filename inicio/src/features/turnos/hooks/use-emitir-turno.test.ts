import { act, renderHook } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { useEmitirTurno } from './use-emitir-turno'
import { TURNOS_API } from '../api/endpoints'

const callMock = vi.fn()

vi.mock('frappe-react-sdk', () => ({
  useFrappePostCall: (method: string) => {
    callMock._method = method
    return { call: callMock }
  },
}))

describe('useEmitirTurno', () => {
  beforeEach(() => {
    callMock.mockReset()
  })

  it('llama al metodo whitelist de emision', async () => {
    callMock.mockResolvedValue({ message: { numero: 7, fecha: '2026-09-03' } })

    const { result } = renderHook(() => useEmitirTurno())
    let emitido
    await act(async () => {
      emitido = await result.current.emitirTurno()
    })

    expect(callMock._method).toBe(TURNOS_API.emitirTurno)
    expect(emitido).toEqual({ numero: 7, fecha: '2026-09-03' })
  })

  it('rechaza una respuesta sin numero', async () => {
    callMock.mockResolvedValue({ message: {} })

    const { result } = renderHook(() => useEmitirTurno())

    await expect(result.current.emitirTurno()).rejects.toThrow(/respuesta invalida al emitir el turno/i)
  })
})
