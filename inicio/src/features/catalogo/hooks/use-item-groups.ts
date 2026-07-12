import { useFrappeGetCall } from 'frappe-react-sdk'
import { CATALOGO_API } from '../api/endpoints'
import { mapItemGroupsResponse } from '../api/mappers'

export function useItemGroups() {
  const { data, isLoading } = useFrappeGetCall<{ message: unknown }>(CATALOGO_API.listItemGroups)

  return {
    groups: mapItemGroupsResponse(data?.message),
    isLoading,
  }
}
