import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AppShell } from './app-shell'

const logoutMock = vi.fn().mockResolvedValue(undefined)
const navigateMock = vi.fn()

vi.mock('frappe-react-sdk', () => ({
  useFrappeAuth: () => ({
    currentUser: 'vendedor@test.cl',
    logout: logoutMock,
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

describe('AppShell', () => {
  beforeEach(() => {
    logoutMock.mockClear()
    navigateMock.mockClear()
  })

  afterEach(() => {
    cleanup()
  })

  it('muestra marca, titulo y usuario', () => {
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AppShell pageTitle="Catalogo terreno">
          <p>contenido</p>
        </AppShell>
      </MemoryRouter>
    )
    expect(screen.getByText('BarrioFarma')).toBeTruthy()
    expect(screen.getByText('Catalogo terreno')).toBeTruthy()
    expect(screen.getByText('vendedor@test.cl')).toBeTruthy()
    expect(screen.getByText('contenido')).toBeTruthy()
  })

  it('logout navega a login', async () => {
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AppShell pageTitle="Catalogo">
          <p>contenido</p>
        </AppShell>
      </MemoryRouter>
    )
    fireEvent.click(screen.getByRole('button', { name: /cerrar sesion/i }))
    await vi.waitFor(() => {
      expect(logoutMock).toHaveBeenCalled()
      expect(navigateMock).toHaveBeenCalledWith('/inicio/login', { replace: true })
    })
  })
})
