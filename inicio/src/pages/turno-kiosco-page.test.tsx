import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import TurnoKioscoPage from '@/pages/turno-kiosco-page'

const emitirTurnoMock = vi.fn()
const isSubmittingState = { value: false }

vi.mock('@/features/turnos/hooks/use-emitir-turno', () => ({
  useEmitirTurno: () => ({
    emitirTurno: emitirTurnoMock,
    isSubmitting: isSubmittingState.value,
  }),
}))

function renderKiosco() {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <TurnoKioscoPage />
    </MemoryRouter>,
  )
}

describe('TurnoKioscoPage', () => {
  beforeEach(() => {
    emitirTurnoMock.mockReset()
    isSubmittingState.value = false
  })

  afterEach(() => {
    cleanup()
  })

  it('emite un turno al tocar y muestra el numero', async () => {
    emitirTurnoMock.mockResolvedValue({ numero: 8 })
    renderKiosco()

    fireEvent.click(screen.getByRole('button', { name: /tocar para obtener numero/i }))

    await waitFor(() => {
      expect(screen.getByText('8')).toBeTruthy()
    })
    expect(screen.getByText(/aguarde a ser llamado/i)).toBeTruthy()
  })

  it('muestra el error y permite reintentar', async () => {
    emitirTurnoMock.mockRejectedValue(new Error('No se pudo emitir el turno. Intente nuevamente.'))
    renderKiosco()

    fireEvent.click(screen.getByRole('button', { name: /tocar para obtener numero/i }))

    await waitFor(() => {
      expect(screen.getByText(/no se pudo emitir el turno/i)).toBeTruthy()
    })
  })
})
