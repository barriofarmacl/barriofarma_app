/**
 * Contenido estatico de la landing publica (V1).
 * Actualizar aqui telefono y horarios tras validacion de negocio.
 */

export const SECTION_IDS = {
  hero: 'hero',
  categorias: 'categorias',
  servicios: 'servicios',
  contacto: 'contacto',
} as const

export const SITE = {
  brand: 'Barriofarma',
  tagline: 'Cerca de tí',
  seo: {
    title: 'Barriofarma — Farmacia de Barrio, Santiago',
    description:
      'Farmacia Barriofarma: asesoria farmaceutica, medicamentos y productos de cuidado personal. Visitanos en La Florida. Atencion presencial; sin venta online.',
  },
} as const

/** URL publica del logo (Vite `public/bf.svg`, respeta `base` en build). */
export const assetBfSvg = `${import.meta.env.BASE_URL}bf.svg`

export const CONTACT = {
  addressLine: 'Rojas Magallanes 94-B, La Florida, Santiago',
  addressShort: 'Rojas Magallanes 94-B, La Florida',
  schedule: [
    'Lunes a viernes: 10:00 - 19:00',
    'Sabados: 10:00 - 14:00',
  ],
  /** Sustituir cuando negocio confirme numero publico. */
  phoneDisplay: '+56 9 XXXX XXXX',
  email: 'contacto@barriofarma.cl',
} as const

export const NAV_LINKS = [
  { href: `#${SECTION_IDS.hero}`, label: 'Inicio' },
  { href: `#${SECTION_IDS.categorias}`, label: 'Categorias' },
  { href: `#${SECTION_IDS.servicios}`, label: 'Servicios' },
  { href: `#${SECTION_IDS.contacto}`, label: 'Contacto' },
] as const

export const HERO = {
  title: 'Tu salud es nuestra prioridad',
  subtitle:
    'Asesoria profesional y productos farmaceuticos con foco en atencion presencial en nuestra sucursal. No vendemos a traves de esta web; visítanos o contáctanos.',
  ctaLabel: 'Ver servicios',
  ctaHref: `#${SECTION_IDS.servicios}`,
  imageAlt: 'Marca Barriofarma',
} as const

export const CATEGORIES = [
  {
    title: 'Medicamentos',
    description: 'Dispensacion segun normativa; recetas retidas segun politica interna.',
  },
  {
    title: 'Dermocosmetica',
    description: 'Productos para el cuidado de la piel con orientacion profesional.',
  },
  {
    title: 'Suplementos y nutricion',
    description: 'Complementos alimenticios; consulta disponibilidad en tienda.',
  },
  {
    title: 'Cuidado personal',
    description: 'Higiene y bienestar para toda la familia.',
  },
] as const

export const SERVICES = [
  {
    title: 'Asesoria farmaceutica',
    body: 'Resolver dudas sobre uso racional de medicamentos y orientacion general.',
  },
  {
    title: 'Atencion con receta medica',
    body: 'Revision de recetas y dispensacion alineada a normativa vigente.',
  },
  {
    title: 'Retiro en farmacia',
    body: 'Todos los productos se entregan en sucursal; sin envios ni checkout web.',
  },
] as const

export const FOOTER_QUICK = [
  { href: `#${SECTION_IDS.hero}`, label: 'Inicio' },
  { href: `#${SECTION_IDS.servicios}`, label: 'Servicios' },
  { href: `#${SECTION_IDS.contacto}`, label: 'Contacto' },
] as const
