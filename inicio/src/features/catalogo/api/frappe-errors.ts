/**
 * Normaliza errores de frappe-react-sdk / Frappe API para UX en catalogo terreno.
 */

type FrappeApiError = {
  message?: string | string[]
  exc?: string
  exception?: string
  _server_messages?: string
}

export function parseFrappeServerMessages(raw?: string): string | null {
  if (!raw) return null
  try {
    const messages = JSON.parse(raw) as unknown[]
    if (!Array.isArray(messages) || messages.length === 0) return null
    const first = JSON.parse(String(messages[0])) as { message?: string }
    return first.message?.trim() || null
  } catch {
    return null
  }
}

function firstStringMessage(message: string | string[] | undefined): string | null {
  if (typeof message === 'string' && message.trim()) return message.trim()
  if (Array.isArray(message) && message.length > 0) {
    const first = String(message[0]).trim()
    return first || null
  }
  return null
}

export function getCatalogoErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof Error && err.message.trim()) {
    return err.message.trim()
  }
  if (err && typeof err === 'object') {
    const e = err as FrappeApiError
    const fromServer = parseFrappeServerMessages(e._server_messages)
    if (fromServer) return fromServer
    const fromMessage = firstStringMessage(e.message)
    if (fromMessage) return fromMessage
    if (typeof e.exc === 'string' && e.exc.trim()) return e.exc.trim()
    if (typeof e.exception === 'string' && e.exception.trim()) return e.exception.trim()
  }
  return fallback
}
