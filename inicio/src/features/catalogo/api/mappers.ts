import type { CatalogItem, CustomerOption, ItemGroupOption, SalesOrderResult } from './types'

export function mapCatalogItemsResponse(raw: unknown): CatalogItem[] {
  if (!Array.isArray(raw)) return []
  return raw.map((row) => {
    const item = row as Record<string, unknown>
    return {
      item_code: String(item.item_code ?? ''),
      item_name: String(item.item_name ?? ''),
      item_group: String(item.item_group ?? ''),
      image: (item.image as string | null | undefined) ?? null,
      uom: String(item.uom ?? ''),
      rate: Number(item.rate ?? 0),
      stock_qty: Number(item.stock_qty ?? 0),
      custom_control_level: String(item.custom_control_level ?? ''),
    }
  })
}

export function mapCustomersResponse(raw: unknown): CustomerOption[] {
  if (!Array.isArray(raw)) return []
  return raw.map((row) => {
    const customer = row as Record<string, unknown>
    return {
      name: String(customer.name ?? ''),
      customer_name: String(customer.customer_name ?? ''),
    }
  })
}

export function mapItemGroupsResponse(raw: unknown): ItemGroupOption[] {
  if (!Array.isArray(raw)) return []
  return raw.map((row) => {
    const group = row as Record<string, unknown>
    return { name: String(group.name ?? '') }
  })
}

export function mapSalesOrderResult(raw: unknown): SalesOrderResult {
  const payload = (raw as { message?: SalesOrderResult })?.message ?? raw
  const order = payload as Record<string, unknown>
  return {
    name: String(order.name ?? ''),
    status: String(order.status ?? ''),
  }
}
