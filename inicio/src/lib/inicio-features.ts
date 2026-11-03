/** Catalogo terreno: boot del sitio gana; build UAT puede fijar VITE_CATALOGO_TERRENO=0. */
export function isCatalogoTerrenoEnabled(): boolean {
  const env = import.meta.env.VITE_CATALOGO_TERRENO
  if (env === '0' || env === 'false') {
    return false
  }

  // @ts-expect-error Frappe boot inyectado en runtime.
  const fromBoot = window.frappe?.boot?.inicio_catalogo_terreno_enabled
  if (fromBoot === 0 || fromBoot === false) {
    return false
  }
  if (fromBoot === 1 || fromBoot === true) {
    return true
  }

  return true
}
