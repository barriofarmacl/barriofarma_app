import { Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import type { CatalogItem } from '../api/types'

type ItemCardProps = {
  item: CatalogItem
  onAdd: (item: CatalogItem) => void
}

function controlBadge(controlLevel: string | undefined) {
  if (!controlLevel) return null
  const isRed = controlLevel.toLowerCase().includes('estupefaciente')
  const color = isRed ? 'text-red-600 bg-red-50 border-red-200' : 'text-green-700 bg-green-50 border-green-200'
  const label = isRed ? 'Estrella Roja' : 'Estrella Verde'
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border ${color}`}>
      <Star className="h-3 w-3 fill-current" aria-hidden />
      {label}
    </span>
  )
}

export default function ItemCard({ item, onAdd }: ItemCardProps) {
  const hasControl = Boolean(item.custom_control_level)

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base leading-tight">{item.item_name}</CardTitle>
          {controlBadge(item.custom_control_level)}
        </div>
        <p className="text-xs text-muted-foreground">{item.item_code}</p>
      </CardHeader>
      <CardContent className="flex-1 space-y-2 text-sm">
        <p>
          Precio: <span className="font-medium">${item.rate.toLocaleString('es-CL')}</span>
        </p>
        <p>
          Stock: <span className="font-medium">{item.stock_qty}</span> {item.uom}
        </p>
        {hasControl && (
          <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2">
            Medicamento con limitantes de venta. La orden puede ser rechazada por el farmaceutico
            si no se cumplen los requisitos de receta al dispensar.
          </p>
        )}
      </CardContent>
      <CardFooter>
        <Button className="w-full" onClick={() => onAdd(item)}>
          Agregar al carrito
        </Button>
      </CardFooter>
    </Card>
  )
}
