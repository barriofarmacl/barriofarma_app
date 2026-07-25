import { useState } from 'react'
import { Loader2, ShoppingCart } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import CartDrawer from '@/features/catalogo/components/cart-drawer'
import CustomerSelect from '@/features/catalogo/components/customer-select'
import ItemGrid from '@/features/catalogo/components/item-grid'
import PriceListSelect from '@/features/catalogo/components/price-list-select'
import { CartProvider, useCart } from '@/features/catalogo/context/cart-context'
import { useCatalogItems } from '@/features/catalogo/hooks/use-catalog-items'
import { useCreateSalesOrder } from '@/features/catalogo/hooks/use-create-sales-order'
import { useItemGroups } from '@/features/catalogo/hooks/use-item-groups'
import type { CatalogItem } from '@/features/catalogo/api/types'

function CatalogoContent() {
  const { dispatch, state, totalQty } = useCart()
  const [priceList, setPriceList] = useState('')
  const [itemGroup, setItemGroup] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [customer, setCustomer] = useState('')
  const [cartOpen, setCartOpen] = useState(false)

  const { items, isLoading } = useCatalogItems({ priceList, searchTerm, itemGroup })
  const { groups } = useItemGroups()
  const { createSalesOrder, isSubmitting } = useCreateSalesOrder()

  const handleAdd = (item: CatalogItem) => {
    dispatch({
      type: 'ADD_ITEM',
      payload: {
        item_code: item.item_code,
        item_name: item.item_name,
        rate: item.rate,
        uom: item.uom,
        custom_control_level: item.custom_control_level,
      },
    })
    setCartOpen(true)
  }

  const handleCreateOrder = async () => {
    if (!customer) {
      toast.error('Seleccione un cliente')
      return
    }
    if (!state.items.length) {
      toast.error('El carrito esta vacio')
      return
    }
    if (!priceList) {
      toast.error('Seleccione una lista de precios')
      return
    }

    try {
      const order = await createSalesOrder({
        customer,
        price_list: priceList,
        items: state.items.map((i) => ({
          item_code: i.item_code,
          qty: i.qty,
          rate: i.rate,
        })),
      })
      toast.success(`Orden ${order.name} creada`)
      dispatch({ type: 'CLEAR' })
      setCartOpen(false)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'No se pudo crear la orden de venta')
    }
  }

  return (
    <>
      <main className="max-w-7xl mx-auto p-4 space-y-6">
        <div className="flex justify-end">
          <Button variant="outline" onClick={() => setCartOpen(true)} className="gap-2">
            <ShoppingCart className="h-4 w-4" />
            Carrito ({totalQty})
          </Button>
        </div>
        <section className="grid md:grid-cols-2 gap-4 bf-surface-card p-4">
          <PriceListSelect value={priceList} onChange={setPriceList} />
          <CustomerSelect value={customer} onChange={setCustomer} />
        </section>

        <section className="bf-surface-card p-4 space-y-3">
          <div className="grid md:grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="search">Buscar</Label>
              <Input
                id="search"
                placeholder="Codigo o nombre..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-group">Grupo</Label>
              <select
                id="item-group"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={itemGroup}
                onChange={(e) => setItemGroup(e.target.value)}
              >
                <option value="">Todos</option>
                {groups.map((g) => (
                  <option key={g.name} value={g.name}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        <ItemGrid items={items} loading={isLoading} onAdd={handleAdd} />

        <div className="sticky bottom-4 flex justify-end">
          <Button disabled={isSubmitting || !state.items.length} onClick={() => void handleCreateOrder()}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generando...
              </>
            ) : (
              'Generar Orden de Venta'
            )}
          </Button>
        </div>
      </main>

      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)} />
    </>
  )
}

export default function CatalogoPage() {
  return (
    <CartProvider>
      <CatalogoContent />
    </CartProvider>
  )
}
