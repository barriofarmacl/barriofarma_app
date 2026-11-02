import { describe, expect, it } from 'vitest'
import {
  classifyControlLevel,
  controlBadgeLabel,
  isControlledMedication,
  normalizeControlLevelForUi,
} from './control-level'

describe('classifyControlLevel', () => {
  it('trata None/vacio como venta libre', () => {
    expect(classifyControlLevel(undefined)).toBe('none')
    expect(classifyControlLevel(null)).toBe('none')
    expect(classifyControlLevel('')).toBe('none')
    expect(classifyControlLevel('None')).toBe('none')
    expect(classifyControlLevel('  none  ')).toBe('none')
  })

  it('detecta psicotropico y estupefaciente', () => {
    expect(classifyControlLevel('Psicotrópico')).toBe('psicotropico')
    expect(classifyControlLevel('Psicotropico')).toBe('psicotropico')
    expect(classifyControlLevel('Estupefaciente')).toBe('estupefaciente')
  })
})

describe('isControlledMedication', () => {
  it('solo true para niveles controlados', () => {
    expect(isControlledMedication('None')).toBe(false)
    expect(isControlledMedication('Psicotrópico')).toBe(true)
    expect(isControlledMedication('Estupefaciente')).toBe(true)
  })
})

describe('controlBadgeLabel', () => {
  it('no muestra badge en venta libre', () => {
    expect(controlBadgeLabel('None')).toBeNull()
  })

  it('asigna estrella verde/roja segun nivel', () => {
    expect(controlBadgeLabel('Psicotrópico')).toBe('Estrella Verde')
    expect(controlBadgeLabel('Estupefaciente')).toBe('Estrella Roja')
  })
})

describe('normalizeControlLevelForUi', () => {
  it('elimina None del payload de UI', () => {
    expect(normalizeControlLevelForUi('None')).toBeUndefined()
    expect(normalizeControlLevelForUi('Psicotrópico')).toBe('Psicotrópico')
  })
})
