import { useEffect, useMemo } from 'react'
import { useFrappeGetCall } from 'frappe-react-sdk'
import { CATALOGO_API } from '../api/endpoints'
import { mapCatalogItemsResponse } from '../api/mappers'
import type { CatalogItem } from '../api/types'

export type CatalogFilters = {
  priceList: string
  searchTerm: string
  itemGroup: string
}

export function useCatalogItems(filters: CatalogFilters) {
  const catalogArgs = useMemo(() => {
    if (!filters.priceList) return null
    return {
      price_list: filters.priceList,
      search_term: filters.searchTerm || undefined,
      item_group: filters.itemGroup || undefined,
      start: 0,
      page_length: 24,
    }
  }, [filters.priceList, filters.searchTerm, filters.itemGroup])

  const { data, isLoading, mutate } = useFrappeGetCall<{ message: unknown }>(
    CATALOGO_API.listCatalogItems,
    catalogArgs ?? undefined,
    catalogArgs ? undefined : null
  )

  useEffect(() => {
    if (filters.priceList && catalogArgs) {
      mutate()
    }
  }, [filters.priceList, filters.searchTerm, filters.itemGroup, catalogArgs, mutate])

  const items: CatalogItem[] = mapCatalogItemsResponse(data?.message)

  return {
    items,
    isLoading: isLoading && Boolean(filters.priceList),
    refresh: mutate,
  }
}
