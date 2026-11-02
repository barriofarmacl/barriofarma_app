type FrappeApiError = {
  message?: string | string[]
  exc?: string
  exception?: string
  httpStatus?: number
  httpStatusText?: string
}

function firstStringMessage(message: string | string[] | undefined): string | null {
  if (typeof message === 'string' && message.trim()) return message.trim()
  if (Array.isArray(message) && message.length > 0) {
    const first = String(message[0]).trim()
    return first || null
  }
  return null
}

export function getTurnosErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof Error && err.message.trim()) {
    const normalized = normalizeKnownTurnosError(err.message.trim())
    if (normalized) return normalized
  }
  if (err && typeof err === 'object') {
    const e = err as FrappeApiError
    const fromMessage = firstStringMessage(e.message)
    if (fromMessage) {
      const normalized = normalizeKnownTurnosError(fromMessage)
      if (normalized) return normalized
      return fromMessage
    }
  }
  return fallback
}

function normalizeKnownTurnosError(message: string): string | null {
  if (/AuthenticationError|Inicie sesion|not logged in|session expired|403|401/i.test(message)) {
    return 'Sesion expirada. Vuelva a iniciar sesion.'
  }
  if (/PermissionError|permiso para acceder|permiso denegado|not permitted|permission/i.test(message)) {
    return 'Este dispositivo no puede emitir turnos. Verifique el usuario del kiosco.'
  }
  return null
}

export function isSessionExpiredError(err: unknown): boolean {
  const message = getTurnosErrorMessage(err, '')
  return /sesion expirada/i.test(message)
}
