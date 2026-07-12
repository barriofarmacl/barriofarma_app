import { useEffect, useMemo } from 'react'
import { useFrappeGetDocList } from 'frappe-react-sdk'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'

type PriceListSelectProps = {
  value: string
  onChange: (priceList: string) => void
}

export default function PriceListSelect({ value, onChange }: PriceListSelectProps) {
  const { data, isLoading } = useFrappeGetDocList<{ name: string; price_list_name?: string }>(
    'Price List',
    {
      fields: ['name', 'price_list_name'],
      filters: [['enabled', '=', 1], ['selling', '=', 1]],
      orderBy: { field: 'name', order: 'asc' },
      limit: 50,
    }
  )

  const lists = useMemo(() => data ?? [], [data])

  useEffect(() => {
    if (!value && lists[0]?.name) {
      onChange(lists[0].name)
    }
  }, [value, lists, onChange])

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Cargando listas de precio...</p>
  }

  if (!lists.length) {
    return <p className="text-sm text-red-600">No hay Price List de venta habilitadas.</p>
  }

  return (
    <div className="space-y-2">
      <Label>Lista de precios</Label>
      <RadioGroup value={value || lists[0]?.name} onValueChange={onChange}>
        {lists.map((pl) => (
          <div key={pl.name} className="flex items-center space-x-2">
            <RadioGroupItem value={pl.name} id={`pl-${pl.name}`} />
            <Label htmlFor={`pl-${pl.name}`}>{pl.price_list_name || pl.name}</Label>
          </div>
        ))}
      </RadioGroup>
    </div>
  )
}
