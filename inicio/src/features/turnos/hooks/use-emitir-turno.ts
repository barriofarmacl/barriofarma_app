import { useCallback, useState } from 'react'
import { useFrappePostCall } from 'frappe-react-sdk'
import { TURNOS_API } from '../api/endpoints'
import { getTurnosErrorMessage } from '../api/errors'
import type { EmitirTurnoResponse } from '../api/types'

type FrappePostResult = {
  message?: EmitirTurnoResponse
  numero?: number
}

export function useEmitirTurno() {
  const { call } = useFrappePostCall(TURNOS_API.emitirTurno)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const emitirTurno = useCallback(async (): Promise<EmitirTurnoResponse> => {
    setIsSubmitting(true)
    try {
      const result = (await call({})) as FrappePostResult
      const payload = result?.message ?? result
      const numero = Number(payload?.numero)
      if (!Number.isFinite(numero) || numero < 1) {
        throw new Error('Respuesta invalida al emitir el turno')
      }
      return { numero, fecha: payload?.fecha }
    } catch (err) {
      throw new Error(getTurnosErrorMessage(err, 'No se pudo emitir el turno. Intente nuevamente.'))
    } finally {
      setIsSubmitting(false)
    }
  }, [call])

  return { emitirTurno, isSubmitting }
}
