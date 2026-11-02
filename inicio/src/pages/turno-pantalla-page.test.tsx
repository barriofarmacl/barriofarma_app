import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import TurnoPantallaPage from '@/pages/turno-pantalla-page'

const pantallaState = {
  numero: null as number | null,
  isLoading: false,
}

vi.mock('@/features/turnos/hooks/use-turno-en-atencion', () => ({
  useTurnoEnAtencion: () => pantallaState,
}))

describe('TurnoPantallaPage', () => {
  afterEach(() => {
    cleanup()
    pantallaState.numero = null
    pantallaState.isLoading = false
  })

  it('muestra espera cuando no hay turno en atencion', () => {
    render(<TurnoPantallaPage />)
    expect(screen.getByText(/espere su turno/i)).toBeTruthy()
  })

  it('muestra el numero en atencion', () => {
    pantallaState.numero = 12
    render(<TurnoPantallaPage />)
    expect(screen.getByTestId('turno-en-atencion').textContent).toBe('12')
  })
})
