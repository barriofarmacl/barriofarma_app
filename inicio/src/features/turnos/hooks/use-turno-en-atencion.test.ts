import { createContext } from 'react'
import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { useTurnoEnAtencion, TURNO_PANTALLA_EVENT } from './use-turno-en-atencion'
import { TURNOS_API } from '../api/endpoints'

const getCallMock = vi.fn()
const mutateMock = vi.fn()
let eventHandler: ((payload: unknown) => void) | null = null

const { esperarGetMock } = vi.hoisted(() => ({
  esperarGetMock: vi.fn(() => new Promise(() => {})),
}))

vi.mock('frappe-react-sdk', () => ({
  FrappeContext: createContext({
    call: { get: (...args: unknown[]) => esperarGetMock(...args) },
  }),
  useFrappeGetCall: (...args: unknown[]) => {
    getCallMock(...args)
    return {
      data: getCallMock._data,
      isLoading: false,
      error: null,
      mutate: mutateMock,
    }
  },
  useFrappeEventListener: (eventName: string, callback: (payload: unknown) => void) => {
    if (eventName === TURNO_PANTALLA_EVENT) {
      eventHandler = callback
    }
  },
}))

describe('useTurnoEnAtencion', () => {
  beforeEach(() => {
    getCallMock.mockReset()
    mutateMock.mockReset()
    esperarGetMock.mockClear()
    eventHandler = null
    getCallMock._data = { message: { numero: 12, desde: '2026-09-03 10:00:00' } }
  })

  it('carga inicial por HTTP sin poll periodico', () => {
    const { result } = renderHook(() => useTurnoEnAtencion())

    expect(getCallMock).toHaveBeenCalledWith(TURNOS_API.turnoEnAtencion)
    expect(result.current.numero).toBe(12)
  })

  it('abre long-poll same-origin para no depender del puerto 9001', async () => {
    renderHook(() => useTurnoEnAtencion())

    await waitFor(() => {
      expect(esperarGetMock).toHaveBeenCalled()
    })
    expect(esperarGetMock.mock.calls[0][0]).toBe(TURNOS_API.esperarTurnoEnAtencion)
  })

  it('actualiza el cache SWR al recibir el evento realtime', () => {
    renderHook(() => useTurnoEnAtencion())

    expect(eventHandler).toBeTypeOf('function')
    act(() => {
      eventHandler?.({ numero: 15, desde: '2026-09-03 10:05:00' })
    })

    expect(mutateMock).toHaveBeenCalledWith(
      { message: { numero: 15, desde: '2026-09-03 10:05:00' } },
      { revalidate: false },
    )
  })

  it('pinta el numero del evento aunque SWR aun no haya mutado', () => {
    const { result } = renderHook(() => useTurnoEnAtencion())

    act(() => {
      eventHandler?.({ numero: 21, desde: '2026-09-03 10:06:00' })
    })

    expect(result.current.numero).toBe(21)
  })

  it('acepta el payload anidado en message', () => {
    const { result } = renderHook(() => useTurnoEnAtencion())

    act(() => {
      eventHandler?.({ message: { numero: 22, desde: '2026-09-03 10:07:00' } })
    })

    expect(result.current.numero).toBe(22)
  })

  it('trata una respuesta vacia como sala sin atencion', () => {
    getCallMock._data = { message: {} }

    const { result } = renderHook(() => useTurnoEnAtencion())

    expect(result.current.numero).toBeNull()
  })
})
