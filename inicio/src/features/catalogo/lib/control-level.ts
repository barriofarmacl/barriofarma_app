/** Valores canónicos de Item.custom_control_level (Select ERPNext). */
export type ControlLevelKind = 'none' | 'psicotropico' | 'estupefaciente' | 'other'

const NONE_VALUES = new Set(['none', 'null', ''])

function normalizeToken(value: string): string {
  return value
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .trim()
    .toLowerCase()
}

/** Clasifica el nivel de control; venta libre (None/vacío) => `none`. */
export function classifyControlLevel(value: string | null | undefined): ControlLevelKind {
  if (value == null) return 'none'
  const token = normalizeToken(String(value))
  if (!token || NONE_VALUES.has(token)) return 'none'
  if (token.includes('estupefaciente')) return 'estupefaciente'
  if (token.includes('psicotrop')) return 'psicotropico'
  return 'other'
}

export function isControlledMedication(value: string | null | undefined): boolean {
  const kind = classifyControlLevel(value)
  return kind === 'psicotropico' || kind === 'estupefaciente'
}

export function controlBadgeLabel(value: string | null | undefined): 'Estrella Verde' | 'Estrella Roja' | null {
  const kind = classifyControlLevel(value)
  if (kind === 'psicotropico') return 'Estrella Verde'
  if (kind === 'estupefaciente') return 'Estrella Roja'
  return null
}

/** Normaliza para el modelo de UI: solo niveles controlados conservan texto. */
export function normalizeControlLevelForUi(value: string | null | undefined): string | undefined {
  return isControlledMedication(value) ? String(value).trim() : undefined
}
