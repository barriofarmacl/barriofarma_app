import ItemCard from './item-card'
import type { CatalogItem } from '../api/types'

type ItemGridProps = {
  items: CatalogItem[]
  loading?: boolean
  onAdd: (item: CatalogItem) => void
}

export default function ItemGrid({ items, loading, onAdd }: ItemGridProps) {
  if (loading) {
    return <p className="text-sm text-muted-foreground">Cargando catalogo...</p>
  }
  if (!items.length) {
    return <p className="text-sm text-muted-foreground">No hay productos para los filtros seleccionados.</p>
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
      {items.map((item) => (
        <ItemCard key={item.item_code} item={item} onAdd={onAdd} />
      ))}
    </div>
  )
}
