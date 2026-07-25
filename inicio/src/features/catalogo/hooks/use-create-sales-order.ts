import { useCallback, useState } from 'react'
import { useFrappePostCall } from 'frappe-react-sdk'
import { CATALOGO_API } from '../api/endpoints'
import { getCatalogoErrorMessage } from '../api/frappe-errors'
import { mapSalesOrderResult } from '../api/mappers'
import type { CreateSalesOrderPayload, SalesOrderResult } from '../api/types'

export function useCreateSalesOrder() {
  const { call } = useFrappePostCall(CATALOGO_API.createSalesOrder)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const createSalesOrder = useCallback(
    async (payload: CreateSalesOrderPayload): Promise<SalesOrderResult> => {
      setIsSubmitting(true)
      try {
        const result = await call(payload)
        return mapSalesOrderResult(result)
      } catch (err) {
        throw new Error(getCatalogoErrorMessage(err, 'No se pudo crear la orden de venta'))
      } finally {
        setIsSubmitting(false)
      }
    },
    [call]
  )

  return { createSalesOrder, isSubmitting }
}
