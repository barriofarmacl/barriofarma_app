/**
 * Normaliza mensajes de error devueltos por Frappe / frappe-js-sdk en login.
 */

type FrappeLoginError = {
  message?: string | string[]
  exc_type?: string
  exception?: string
}

export function getLoginErrorMessage(err: unknown): string {
  if (err && typeof err === 'object') {
    const e = err as FrappeLoginError
    const { message } = e
    if (typeof message === 'string' && message.trim()) return message
    if (Array.isArray(message) && message.length > 0) {
      return String(message[0])
    }
    if (typeof e.exception === 'string' && e.exception.trim()) return e.exception
  }
  if (err instanceof Error && err.message) return err.message
  return 'No se pudo iniciar sesion. Verifica correo y contrasena.'
}
