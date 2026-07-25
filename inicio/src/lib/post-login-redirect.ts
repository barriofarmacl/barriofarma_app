export const DESK_PATH = '/app'
export const CATALOGO_PATH = '/inicio/catalogo'

export const POST_LOGIN_PATH_API =
  'barriofarma_app.barriofarma_app.api.catalogo_terreno.get_post_login_path'

type FrappeMethodResponse = {
  message?: string
  exc?: string
  _server_messages?: string
}

/** Normaliza la ruta devuelta por el backend (solo rutas internas conocidas). */
export function normalizePostLoginPath(path: unknown): string {
  if (path === CATALOGO_PATH) return CATALOGO_PATH
  return DESK_PATH
}

export async function fetchPostLoginPath(): Promise<string> {
  const response = await fetch(`/api/method/${POST_LOGIN_PATH_API}`, {
    method: 'GET',
    credentials: 'include',
    headers: { Accept: 'application/json' },
  })

  const payload = (await response.json()) as FrappeMethodResponse
  if (!response.ok || payload.exc) {
    throw new Error('No se pudo resolver el destino post-login')
  }

  return normalizePostLoginPath(payload.message)
}
