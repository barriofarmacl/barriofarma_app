import { describe, expect, it } from 'vitest'
import { cartReducer, initialCartState } from '../context/cart-context'

describe('cartReducer', () => {
  it('agrega item nuevo al carrito', () => {
    const next = cartReducer(initialCartState, {
      type: 'ADD_ITEM',
      payload: {
        item_code: 'ITEM-1',
        item_name: 'Paracetamol',
        rate: 1000,
        uom: 'Unidad',
      },
    })
    expect(next.items).toHaveLength(1)
    expect(next.items[0].qty).toBe(1)
  })

  it('incrementa qty de item existente', () => {
    const base = cartReducer(initialCartState, {
      type: 'ADD_ITEM',
      payload: {
        item_code: 'ITEM-1',
        item_name: 'Paracetamol',
        rate: 1000,
        uom: 'Unidad',
      },
    })
    const next = cartReducer(base, {
      type: 'ADD_ITEM',
      payload: {
        item_code: 'ITEM-1',
        item_name: 'Paracetamol',
        rate: 1000,
        uom: 'Unidad',
        qty: 2,
      },
    })
    expect(next.items[0].qty).toBe(3)
  })

  it('quita item al actualizar qty a cero', () => {
    const base = cartReducer(initialCartState, {
      type: 'ADD_ITEM',
      payload: {
        item_code: 'ITEM-1',
        item_name: 'Paracetamol',
        rate: 1000,
        uom: 'Unidad',
      },
    })
    const next = cartReducer(base, {
      type: 'UPDATE_QTY',
      payload: { item_code: 'ITEM-1', qty: 0 },
    })
    expect(next.items).toHaveLength(0)
  })

  it('vacía carrito con CLEAR', () => {
    const base = cartReducer(initialCartState, {
      type: 'ADD_ITEM',
      payload: {
        item_code: 'ITEM-1',
        item_name: 'Paracetamol',
        rate: 1000,
        uom: 'Unidad',
      },
    })
    const next = cartReducer(base, { type: 'CLEAR' })
    expect(next.items).toHaveLength(0)
  })
})
