import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useSearchCustomers } from '../hooks/use-search-customers'

type CustomerSelectProps = {
  value: string
  onChange: (customerName: string) => void
}

export default function CustomerSelect({ value, onChange }: CustomerSelectProps) {
  const [term, setTerm] = useState('')
  const { options, isLoading } = useSearchCustomers(term)

  return (
    <div className="space-y-2">
      <Label htmlFor="customer-search">Cliente</Label>
      <Input
        id="customer-search"
        placeholder="Buscar cliente institucional..."
        value={term}
        onChange={(e) => setTerm(e.target.value)}
      />
      {isLoading && <p className="text-xs text-muted-foreground">Buscando...</p>}
      {options.length > 0 && (
        <ul className="border rounded max-h-40 overflow-auto text-sm">
          {options.map((c) => (
            <li key={c.name}>
              <button
                type="button"
                className={`w-full text-left px-3 py-2 hover:bg-brand-subtle ${
                  value === c.name ? 'bg-accent font-medium' : ''
                }`}
                onClick={() => onChange(c.name)}
              >
                {c.customer_name} ({c.name})
              </button>
            </li>
          ))}
        </ul>
      )}
      {value && <p className="text-xs text-muted-foreground">Seleccionado: {value}</p>}
    </div>
  )
}
