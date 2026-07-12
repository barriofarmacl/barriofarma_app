import React, { createContext, useContext, useMemo, useReducer, type ReactNode } from 'react'

export type CartItem = {
  item_code: string
  item_name: string
  rate: number
  uom: string
  custom_control_level?: string
  qty: number
}

export type CartState = {
  items: CartItem[]
}

export type CartAction =
  | { type: 'ADD_ITEM'; payload: Omit<CartItem, 'qty'> & { qty?: number } }
  | { type: 'UPDATE_QTY'; payload: { item_code: string; qty: number } }
  | { type: 'REMOVE_ITEM'; payload: { item_code: string } }
  | { type: 'CLEAR' }

export const initialCartState: CartState = { items: [] }

export function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case 'ADD_ITEM': {
      const qty = action.payload.qty ?? 1
      const existing = state.items.find((i) => i.item_code === action.payload.item_code)
      if (existing) {
        return {
          items: state.items.map((i) =>
            i.item_code === action.payload.item_code ? { ...i, qty: i.qty + qty } : i
          ),
        }
      }
      return {
        items: [
          ...state.items,
          {
            item_code: action.payload.item_code,
            item_name: action.payload.item_name,
            rate: action.payload.rate,
            uom: action.payload.uom,
            custom_control_level: action.payload.custom_control_level,
            qty,
          },
        ],
      }
    }
    case 'UPDATE_QTY': {
      if (action.payload.qty <= 0) {
        return {
          items: state.items.filter((i) => i.item_code !== action.payload.item_code),
        }
      }
      return {
        items: state.items.map((i) =>
          i.item_code === action.payload.item_code ? { ...i, qty: action.payload.qty } : i
        ),
      }
    }
    case 'REMOVE_ITEM':
      return {
        items: state.items.filter((i) => i.item_code !== action.payload.item_code),
      }
    case 'CLEAR':
      return initialCartState
    default:
      return state
  }
}

type CartContextValue = {
  state: CartState
  dispatch: React.Dispatch<CartAction>
  totalQty: number
  totalAmount: number
}

// Context and provider intentionally share a module to keep the cart boundary cohesive.
// eslint-disable-next-line react-refresh/only-export-components
const CartContext = createContext<CartContextValue | null>(null)

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(cartReducer, initialCartState)
  const value = useMemo(() => {
    const totalQty = state.items.reduce((acc, i) => acc + i.qty, 0)
    const totalAmount = state.items.reduce((acc, i) => acc + i.qty * i.rate, 0)
    return { state, dispatch, totalQty, totalAmount }
  }, [state])

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) {
    throw new Error('useCart debe usarse dentro de CartProvider')
  }
  return ctx
}
