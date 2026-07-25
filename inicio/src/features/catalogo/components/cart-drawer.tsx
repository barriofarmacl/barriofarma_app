import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useCart } from '../context/cart-context'

type CartDrawerProps = {
  open: boolean
  onClose: () => void
}

export default function CartDrawer({ open, onClose }: CartDrawerProps) {
  const { state, dispatch, totalQty, totalAmount } = useCart()

  if (!open) return null

  return (
    <aside className="fixed inset-y-0 right-0 w-full max-w-md bg-card border-l border-border shadow-xl z-40 flex flex-col">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h2 className="text-lg font-semibold text-primary">Carrito ({totalQty})</h2>
        <Button variant="outline" size="sm" onClick={onClose}>
          Cerrar
        </Button>
      </div>
      <ScrollArea className="flex-1 p-4">
        {!state.items.length ? (
          <p className="text-sm text-muted-foreground">El carrito esta vacio.</p>
        ) : (
          <ul className="space-y-3">
            {state.items.map((item) => (
              <li key={item.item_code} className="border rounded p-3">
                <p className="font-medium text-sm">{item.item_name}</p>
                <p className="text-xs text-muted-foreground">{item.item_code}</p>
                <div className="mt-2 flex items-center gap-2">
                  <Input
                    type="number"
                    min={1}
                    className="w-20 h-8"
                    value={item.qty}
                    onChange={(e) =>
                      dispatch({
                        type: 'UPDATE_QTY',
                        payload: { item_code: item.item_code, qty: Number(e.target.value) },
                      })
                    }
                  />
                  <span className="text-sm">${(item.rate * item.qty).toLocaleString('es-CL')}</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      dispatch({ type: 'REMOVE_ITEM', payload: { item_code: item.item_code } })
                    }
                  >
                    Quitar
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </ScrollArea>
      <div className="p-4 border-t">
        <p className="text-sm font-semibold mb-2">Total: ${totalAmount.toLocaleString('es-CL')}</p>
        <Button
          variant="outline"
          className="w-full"
          disabled={!state.items.length}
          onClick={() => dispatch({ type: 'CLEAR' })}
        >
          Vaciar carrito
        </Button>
      </div>
    </aside>
  )
}
