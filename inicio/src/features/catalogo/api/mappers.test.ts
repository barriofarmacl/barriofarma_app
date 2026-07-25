import { describe, expect, it } from 'vitest'
import {
  mapCatalogItemsResponse,
  mapCustomersResponse,
  mapItemGroupsResponse,
  mapSalesOrderResult,
} from './mappers'

describe('mapCatalogItemsResponse', () => {
  it('mapea filas de list_catalog_items', () => {
    const mapped = mapCatalogItemsResponse([
      {
        item_code: 'MED-1',
        item_name: 'Ibuprofeno',
        item_group: 'Medicamentos',
        uom: 'Unidad',
        rate: 2500,
        stock_qty: 12,
        custom_control_level: 'Psicotropico',
      },
    ])
    expect(mapped[0]).toMatchObject({
      item_code: 'MED-1',
      rate: 2500,
      stock_qty: 12,
      custom_control_level: 'Psicotropico',
    })
  })
})

describe('mapCustomersResponse', () => {
  it('mapea filas de search_customers', () => {
    const mapped = mapCustomersResponse([
      { name: 'CUST-001', customer_name: 'Hospital Regional' },
    ])
    expect(mapped[0]).toEqual({
      name: 'CUST-001',
      customer_name: 'Hospital Regional',
    })
  })
})

describe('mapItemGroupsResponse', () => {
  it('mapea filas de list_item_groups', () => {
    expect(mapItemGroupsResponse([{ name: 'Medicamentos' }])).toEqual([{ name: 'Medicamentos' }])
  })
})

describe('mapSalesOrderResult', () => {
  it('extrae name y status del message envelope', () => {
    expect(
      mapSalesOrderResult({ message: { name: 'SO-001', status: 'Draft' } })
    ).toEqual({ name: 'SO-001', status: 'Draft' })
  })
})
