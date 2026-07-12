export type CatalogItem = {
  item_code: string
  item_name: string
  item_group: string
  image?: string | null
  uom: string
  rate: number
  stock_qty: number
  custom_control_level?: string
}

export type CustomerOption = {
  name: string
  customer_name: string
}

export type ItemGroupOption = {
  name: string
}

export type SalesOrderResult = {
  name: string
  status: string
}

export type CreateSalesOrderPayload = {
  customer: string
  price_list: string
  items: Array<{ item_code: string; qty: number; rate: number }>
}
