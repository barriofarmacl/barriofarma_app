import { useCallback, useContext, useEffect, useRef, useState } from 'react'
import {
  FrappeContext,
  useFrappeEventListener,
  useFrappeGetCall,
} from 'frappe-react-sdk'
import { TURNOS_API } from '../api/endpoints'
import type { TurnoEnAtencionResponse } from '../api/types'

/** Evento Socket.IO publicado por api/turnos.py al cambiar el turno en atencion. */
export const TURNO_PANTALLA_EVENT = 'turno_atencion_update'

type FrappeCall = {
  get: (path: string, params?: Record<string, string>) => Promise<unknown>
}

type FrappeGetResult = {
  message?: TurnoEnAtencionResponse
}

function numeroDesdePayload(payload: TurnoEnAtencionResponse | undefined): number | null {
  const numero = Number(payload?.numero)
  return Number.isFinite(numero) && numero >= 1 ? numero : null
}

export function tokenPantalla(payload: TurnoEnAtencionResponse | undefined): string {
  if (!payload || payload.numero == null) {
    return ''
  }
  return `${payload.numero}|${payload.desde ?? ''}`
}

/** Normaliza lo que llega por socket: dict plano o `{ message: dict }`. */
export function payloadDesdeEvento(raw: unknown): TurnoEnAtencionResponse {
  if (!raw || typeof raw !== 'object') {
    return {}
  }
  const obj = raw as Record<string, unknown>
  const anidado = obj.message
  if (
    !('numero' in obj) &&
    anidado &&
    typeof anidado === 'object' &&
    !Array.isArray(anidado)
  ) {
    return anidado as TurnoEnAtencionResponse
  }
  return obj as TurnoEnAtencionResponse
}

function payloadDesdeCall(raw: unknown): TurnoEnAtencionResponse {
  if (!raw || typeof raw !== 'object') {
    return {}
  }
  const obj = raw as Record<string, unknown>
  if (obj.message && typeof obj.message === 'object' && !Array.isArray(obj.message)) {
    return obj.message as TurnoEnAtencionResponse
  }
  return obj as TurnoEnAtencionResponse
}

export function useTurnoEnAtencion() {
  const frappe = useContext(FrappeContext) as { call?: FrappeCall } | null
  const { data, isLoading, error, mutate } = useFrappeGetCall<FrappeGetResult>(
    TURNOS_API.turnoEnAtencion,
  )
  const [push, setPush] = useState<TurnoEnAtencionResponse | null>(null)
  const ultimoRef = useRef<TurnoEnAtencionResponse>({})
  const callRef = useRef(frappe?.call)
  callRef.current = frappe?.call

  const aplicar = useCallback(
    (payload: TurnoEnAtencionResponse) => {
      ultimoRef.current = payload
      setPush(payload)
      void mutate({ message: payload }, { revalidate: false })
    },
    [mutate],
  )
  const aplicarRef = useRef(aplicar)
  aplicarRef.current = aplicar

  const onRealtime = useCallback(
    (raw: unknown) => {
      aplicar(payloadDesdeEvento(raw))
    },
    [aplicar],
  )

  useFrappeEventListener(TURNO_PANTALLA_EVENT, onRealtime)

  useEffect(() => {
    if (data?.message) {
      ultimoRef.current = data.message
    }
  }, [data])

  useEffect(() => {
    let cancelled = false

    const loop = async () => {
      while (!cancelled) {
        const call = callRef.current
        if (!call) {
          await new Promise((resolve) => setTimeout(resolve, 1000))
          continue
        }
        try {
          // MUST llamarse como metodo: FrappeCall.get usa this.axios.
          const raw = await call.get(TURNOS_API.esperarTurnoEnAtencion, {
            visto: tokenPantalla(ultimoRef.current),
          })
          if (cancelled) {
            return
          }
          aplicarRef.current(payloadDesdeCall(raw))
        } catch {
          if (cancelled) {
            return
          }
          await new Promise((resolve) => setTimeout(resolve, 1000))
        }
      }
    }

    void loop()
    return () => {
      cancelled = true
    }
  }, [])

  const inicial = data?.message ?? {}
  const payload = push ?? inicial
  const enAtencion = numeroDesdePayload(payload)

  return {
    numero: enAtencion,
    desde: payload.desde,
    isLoading,
    error,
  }
}
