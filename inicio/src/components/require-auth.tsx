import { Navigate } from 'react-router-dom'
import { useFrappeAuth } from 'frappe-react-sdk'
import { Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { currentUser, isLoading } = useFrappeAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary" aria-label="Cargando" />
      </div>
    )
  }

  if (!currentUser) {
    return <Navigate to="/inicio/login" replace />
  }

  return <>{children}</>
}
