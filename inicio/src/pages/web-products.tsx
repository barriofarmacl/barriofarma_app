// /workspace/development/frappe-bench/apps/barriofarma_app/inicio/src/pages/products.tsx
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"

interface Product {
  id: number
  name: string
  description: string
}

export default function WebProductsPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [searchTerm, setSearchTerm] = useState<string>("")
  const [cart, setCart] = useState<Product[]>([])

  useEffect(() => {
    // Simulando la obtención de productos de una API
    const fetchedProducts: Product[] = [
      { id: 1, name: 'Producto 1', description: 'Descripción del Producto 1' },
      { id: 2, name: 'Producto 2', description: 'Descripción del Producto 2' },
      { id: 3, name: 'Producto 3', description: 'Descripción del Producto 3' },
      { id: 4, name: 'Producto 4', description: 'Descripción del Producto 4' },
      { id: 5, name: 'Producto 5', description: 'Descripción del Producto 5' },
    ]
    setProducts(fetchedProducts)
  }, [])

  const handleAddToCart = (product: Product) => {
    setCart([...cart, product])
  }

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center p-4">
      <Card className="w-full max-w-2xl mb-4">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-purple-700">Buscar Productos</CardTitle>
        </CardHeader>
        <CardContent>
          <Input 
            type="text" 
            placeholder="Buscar productos..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mb-4"
          />
        </CardContent>
      </Card>
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-lg font-bold">Resultados de búsqueda</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {filteredProducts.map(product => (
            <Card key={product.id} className="shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg font-semibold">{product.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">{product.description}</p>
              </CardContent>
              <CardFooter>
                <Button 
                  className="bg-purple-700 hover:bg-purple-800 text-white w-full"
                  onClick={() => handleAddToCart(product)}
                >
                  Agregar al carrito
                </Button>
              </CardFooter>
            </Card>
          ))}
        </CardContent>
      </Card>

      <Card className="w-full max-w-2xl mt-4">
        <CardHeader>
          <CardTitle className="text-lg font-bold">Carrito de Compras</CardTitle>
        </CardHeader>
        <CardContent>
          {cart.length === 0 ? (
            <p className="text-gray-600">Tu carrito está vacío.</p>
          ) : (
            <ul>
              {cart.map((item, index) => (
                <li key={index} className="flex justify-between py-1">
                  <span>{item.name}</span>
                  <span className="text-gray-600">✔️</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}