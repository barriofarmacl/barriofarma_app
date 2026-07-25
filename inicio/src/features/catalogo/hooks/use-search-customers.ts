import { useEffect, useState } from 'react'
import { useFrappeGetCall } from 'frappe-react-sdk'
import { CATALOGO_API } from '../api/endpoints'
import { mapCustomersResponse } from '../api/mappers'
import type { CustomerOption } from '../api/types'

const MIN_SEARCH_LENGTH = 2
const DEBOUNCE_MS = 300

export function useSearchCustomers(searchTerm: string) {
  const [debounced, setDebounced] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(searchTerm), DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchTerm])

  const enabled = debounced.length >= MIN_SEARCH_LENGTH

  const { data, isLoading } = useFrappeGetCall<{ message: unknown }>(
    CATALOGO_API.searchCustomers,
    enabled ? { search_term: debounced } : undefined,
    enabled ? undefined : null
  )

  const options: CustomerOption[] = enabled ? mapCustomersResponse(data?.message) : []

  return { options, isLoading: enabled && isLoading }
}
