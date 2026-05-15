/**
 * Validaciones puras del formulario de login (testeables sin React).
 */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function normalizeLoginUsername(value: string): string {
  return value.trim()
}

/** Devuelve mensaje de error en espanol o null si es valido. */
export function validateLoginEmail(value: string): string | null {
  const v = value.trim()
  if (!v) return 'El correo electronico es obligatorio'
  if (!EMAIL_RE.test(v)) return 'Introduce un correo electronico valido'
  return null
}

/** Devuelve mensaje de error o null si es valido. */
export function validateLoginPassword(value: string): string | null {
  if (!value) return 'La contrasena es obligatoria'
  if (value.length < 6) return 'La contrasena debe tener al menos 6 caracteres'
  return null
}
