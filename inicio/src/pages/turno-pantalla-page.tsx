import { Loader2 } from 'lucide-react'
import { useTurnoEnAtencion } from '@/features/turnos/hooks/use-turno-en-atencion'

export default function TurnoPantallaPage() {
  const { numero, isLoading } = useTurnoEnAtencion()

  return (
    <main className="min-h-screen bg-brand text-brand-foreground flex flex-col items-center justify-center p-6">
      {isLoading && numero == null ? (
        <Loader2 className="h-16 w-16 animate-spin" aria-label="Cargando turno" />
      ) : numero == null ? (
        <>
          <p className="font-display text-4xl sm:text-6xl text-center">Sala de espera</p>
          <p className="mt-6 text-2xl text-brand-foreground/80">Espere su turno</p>
        </>
      ) : (
        <>
          <p className="text-2xl sm:text-3xl uppercase tracking-wide text-brand-foreground/80">
            Turno en atencion
          </p>
          <p
            className="font-display tabular-nums leading-none mt-4"
            style={{ fontSize: 'clamp(8rem, 40vw, 24rem)' }}
            data-testid="turno-en-atencion"
          >
            {numero}
          </p>
        </>
      )}
    </main>
  )
}
