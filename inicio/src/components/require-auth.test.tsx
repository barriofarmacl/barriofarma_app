import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './require-auth'

const authState = vi.hoisted(() => ({
  currentUser: null as string | null,
  isLoading: false,
}))

vi.mock('frappe-react-sdk', () => ({
  useFrappeAuth: () => authState,
}))

function renderProtectedRoute() {
  return render(
    <MemoryRouter
      initialEntries={['/inicio/catalogo']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/inicio/login" element={<p>Inicio de sesion</p>} />
        <Route
          path="/inicio/catalogo"
          element={
            <RequireAuth>
              <p>Catalogo protegido</p>
            </RequireAuth>
          }
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('RequireAuth', () => {
  beforeEach(() => {
    authState.currentUser = null
    authState.isLoading = false
  })

  afterEach(() => {
    cleanup()
  })

  it('muestra estado de carga mientras resuelve la sesion', () => {
    authState.isLoading = true

    renderProtectedRoute()

    expect(screen.getByLabelText('Cargando')).toBeTruthy()
    expect(screen.queryByText('Catalogo protegido')).toBeNull()
  })

  it('redirige al login cuando no existe una sesion', () => {
    renderProtectedRoute()

    expect(screen.getByText('Inicio de sesion')).toBeTruthy()
    expect(screen.queryByText('Catalogo protegido')).toBeNull()
  })

  it('renderiza el contenido protegido para un usuario autenticado', () => {
    authState.currentUser = 'vendedor@test.cl'

    renderProtectedRoute()

    expect(screen.getByText('Catalogo protegido')).toBeTruthy()
  })
})
