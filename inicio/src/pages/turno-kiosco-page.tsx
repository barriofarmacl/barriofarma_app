import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useEmitirTurno } from '@/features/turnos/hooks/use-emitir-turno'
import { isSessionExpiredError } from '@/features/turnos/api/errors'

const MOSTRAR_NUMERO_MS = 12000

type Vista = 'idle' | 'exito' | 'error'

export default function TurnoKioscoPage() {
  const navigate = useNavigate()
  const { emitirTurno, isSubmitting } = useEmitirTurno()
  const [vista, setVista] = useState<Vista>('idle')
  const [numero, setNumero] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reset = useCallback(() => {
    setVista('idle')
    setNumero(null)
    setError(null)
  }, [])

  useEffect(() => {
    if (vista !== 'exito') return
    const timer = window.setTimeout(reset, MOSTRAR_NUMERO_MS)
    return () => window.clearTimeout(timer)
  }, [vista, reset])

  const onEmitir = async () => {
    if (isSubmitting) return
    setError(null)
    try {
      const emitido = await emitirTurno()
      setNumero(emitido.numero)
      setVista('exito')
    } catch (err) {
      if (isSessionExpiredError(err)) {
        navigate('/inicio/login', { replace: true })
        return
      }
      setError(err instanceof Error ? err.message : 'No se pudo emitir el turno. Intente nuevamente.')
      setVista('error')
    }
  }

  if (vista === 'exito' && numero != null) {
    return (
      <main className="min-h-screen bg-brand text-brand-foreground flex flex-col items-center justify-center p-6">
        <p className="text-xl font-medium uppercase tracking-wide text-brand-foreground/80">
          Su numero
        </p>
        <p className="font-display tabular-nums leading-none mt-4" style={{ fontSize: 'clamp(6rem, 28vw, 18rem)' }}>
          {numero}
        </p>
        <p className="mt-8 text-lg text-brand-foreground/80">Aguarde a ser llamado</p>
        <button
          type="button"
          onClick={reset}
          className="mt-10 text-base underline underline-offset-4 text-brand-foreground/70"
        >
          Listo
        </button>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-brand text-brand-foreground flex items-center justify-center p-6">
      <button
        type="button"
        onClick={onEmitir}
        disabled={isSubmitting}
        className="min-h-[70vh] w-full max-w-3xl rounded-3xl bg-primary text-primary-foreground flex flex-col items-center justify-center gap-6 px-8 py-12 text-center shadow-lg disabled:opacity-70"
      >
        {isSubmitting ? (
          <Loader2 className="h-16 w-16 animate-spin" aria-label="Emitiendo turno" />
        ) : (
          <>
            <span className="font-display text-5xl sm:text-6xl leading-tight">
              Tocar para obtener numero
            </span>
            {vista === 'error' && error ? (
              <span className="text-lg text-destructive-foreground bg-destructive/80 rounded-md px-4 py-2">
                {error}
              </span>
            ) : (
              <span className="text-xl text-primary-foreground/80">Un toque, un numero</span>
            )}
          </>
        )}
      </button>
    </main>
  )
}
