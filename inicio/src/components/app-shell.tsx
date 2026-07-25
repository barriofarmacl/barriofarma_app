import { LogOut } from 'lucide-react'
import { useFrappeAuth } from 'frappe-react-sdk'
import { useNavigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'

export type AppShellProps = {
  children: ReactNode
  pageTitle?: string
  headerActions?: ReactNode
}

export function AppShell({ children, pageTitle, headerActions }: AppShellProps) {
  const { currentUser, logout } = useFrappeAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await logout()
    } finally {
      navigate('/inicio/login', { replace: true })
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="bg-card border-b border-border px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-primary tracking-tight font-display">BarrioFarma</p>
            {pageTitle ? (
              <h1 className="text-lg font-bold text-foreground truncate">{pageTitle}</h1>
            ) : null}
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {headerActions}
            {currentUser ? (
              <span
                className="hidden sm:inline text-sm text-muted-foreground truncate max-w-[12rem]"
                title={currentUser}
              >
                {currentUser}
              </span>
            ) : null}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => void handleLogout()}
              aria-label="Cerrar sesion"
            >
              <LogOut className="h-4 w-4" aria-hidden />
              <span className="hidden sm:inline">Salir</span>
            </Button>
          </div>
        </div>
      </header>
      <div className="flex-1">{children}</div>
    </div>
  )
}
