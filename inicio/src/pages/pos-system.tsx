import React, { useState, useEffect } from 'react'
import { Button } from "../components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../components/ui/card"
import { ScrollArea } from "../components/ui/scroll-area"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
import { RadioGroup, RadioGroupItem } from "../components/ui/radio-group"
import { CreditCard, Printer, X, Plus, Minus, ArrowLeft, Search, AlertTriangle } from "lucide-react"
import Image from "next/image"
import { toast } from "../components/ui/use-toast"

const initialInventory = [
  { id: 1, name: "Paracetamol", price: 5.00, stock: 100, description: "Analgésico y antipirético de uso común", image: "/placeholder.svg?height=100&width=100" },
  { id: 2, name: "Ibuprofeno", price: 7.50, stock: 80, description: "Antiinflamatorio no esteroideo", image: "/placeholder.svg?height=100&width=100" },
  { id: 3, name: "Amoxicilina", price: 15.00, stock: 50, description: "Antibiótico de amplio espectro", image: "/placeholder.svg?height=100&width=100" },
  { id: 4, name: "Omeprazol", price: 10.00, stock: 70, description: "Inhibidor de la bomba de protones", image: "/placeholder.svg?height=100&width=100" },
  { id: 5, name: "Loratadina", price: 8.00, stock: 60, description: "Antihistamínico para alergias", image: "/placeholder.svg?height=100&width=100" },
]

export default function Component() {
  const [inventory, setInventory] = useState(initialInventory)
  const [cart, setCart] = useState([])
  const [total, setTotal] = useState(0)
  const [paymentAmount, setPaymentAmount] = useState("")
  const [receipt, setReceipt] = useState(null)
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [showPaymentConfirmation, setShowPaymentConfirmation] = useState(false)
  const [paymentMethod, setPaymentMethod] = useState("efectivo")
  const [amountReceived, setAmountReceived] = useState("")
  const [searchTerm, setSearchTerm] = useState("")
  const [discount, setDiscount] = useState(0)

  useEffect(() => {
    updateTotal()
  }, [cart, discount])

  const addToCart = (product) => {
    if (product.stock > 0) {
      const existingItem = cart.find(item => item.id === product.id)
      if (existingItem) {
        setCart(cart.map(item =>
          item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        ))
      } else {
        setCart([...cart, { ...product, quantity: 1 }])
      }
      setInventory(inventory.map(item =>
        item.id === product.id ? { ...item, stock: item.stock - 1 } : item
      ))
    } else {
      toast({
        title: "Error",
        description: "No hay stock disponible para este producto.",
        variant: "destructive",
      })
    }
  }

  const removeFromCart = (productId) => {
    const updatedCart = cart.map(item =>
      item.id === productId ? { ...item, quantity: Math.max(0, item.quantity - 1) } : item
    ).filter(item => item.quantity > 0)
    setCart(updatedCart)
    setInventory(inventory.map(item =>
      item.id === productId ? { ...item, stock: item.stock + 1 } : item
    ))
  }

  const updateTotal = () => {
    const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
    const discountAmount = subtotal * (discount / 100)
    setTotal(subtotal - discountAmount)
  }

  const handlePayment = () => {
    if (cart.length === 0) {
      toast({
        title: "Error",
        description: "El carrito está vacío. Agregue productos antes de proceder al pago.",
        variant: "destructive",
      })
      return
    }
    setShowPaymentConfirmation(true)
  }

  const handleKeypadClick = (value) => {
    if (value === "clear") {
      setAmountReceived("")
    } else {
      setAmountReceived(prev => prev + value)
    }
  }

  const handleConfirmPayment = () => {
    if (paymentMethod === "efectivo" && parseFloat(amountReceived) < total) {
      toast({
        title: "Error",
        description: "El monto recibido es insuficiente.",
        variant: "destructive",
      })
      return
    }
    const change = paymentMethod === "efectivo" ? parseFloat(amountReceived) - total : 0
    setReceipt({
      items: cart,
      subtotal: cart.reduce((sum, item) => sum + item.price * item.quantity, 0),
      discount: discount,
      total: total,
      paid: paymentMethod === "efectivo" ? parseFloat(amountReceived) : total,
      change: change,
      paymentMethod: paymentMethod
    })
    setCart([])
    setTotal(0)
    setAmountReceived("")
    setShowPaymentConfirmation(false)
    setDiscount(0)
    toast({
      title: "Venta completada",
      description: "La venta se ha procesado correctamente.",
    })
  }

  const handleCancelSale = () => {
    // Restore inventory
    inventory.forEach(invItem => {
      const cartItem = cart.find(item => item.id === invItem.id)
      if (cartItem) {
        invItem.stock += cartItem.quantity
      }
    })
    setInventory([...inventory])
    setCart([])
    setTotal(0)
    setShowPaymentConfirmation(false)
    setDiscount(0)
    toast({
      title: "Venta cancelada",
      description: "La venta ha sido cancelada y el inventario ha sido restaurado.",
    })
  }

  const filteredInventory = inventory
  .filter(product => product.name.toLowerCase().includes(searchTerm.toLowerCase()))
  .slice(0, 5)

  const PaymentConfirmation = () => (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Confirmar Pago</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[200px] w-full rounded-md border p-4 mb-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead>Cantidad</TableHead>
                <TableHead>Precio</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cart.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.quantity}</TableCell>
                  <TableCell>${(item.price * item.quantity).toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
        <div className="text-right mb-4">
          <div>Subtotal: ${cart.reduce((sum, item) => sum + item.price * item.quantity, 0).toFixed(2)}</div>
          <div>Descuento: {discount}%</div>
          <div className="font-bold">Total: ${total.toFixed(2)}</div>
        </div>
        <RadioGroup value={paymentMethod} onValueChange={setPaymentMethod} className="mb-4">
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="efectivo" id="efectivo" />
            <Label htmlFor="efectivo">Efectivo</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="tarjeta" id="tarjeta" />
            <Label htmlFor="tarjeta">Tarjeta</Label>
          </div>
        </RadioGroup>
        {paymentMethod === "efectivo" && (
          <div className="mb-4">
            <Label htmlFor="amountReceived">Monto Recibido</Label>
            <Input
              id="amountReceived"
              value={amountReceived}
              onChange={(e) => setAmountReceived(e.target.value)}
              className="mt-1"
            />
            <div className="grid grid-cols-3 gap-2 mt-2">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, ".", 0, "clear"].map(key => (
                <Button key={key} variant="outline" onClick={() => handleKeypadClick(key)}>
                  {key === "clear" ? <X className="h-4 w-4" /> : key}
                </Button>
              ))}
            </div>
            {parseFloat(amountReceived) >= total && (
              <div className="mt-2 text-right">
                Cambio: ${(parseFloat(amountReceived) - total).toFixed(2)}
              </div>
            )}
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={() => setShowPaymentConfirmation(false)}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Volver
        </Button>
        <Button onClick={handleConfirmPayment} disabled={paymentMethod === "efectivo" && parseFloat(amountReceived) < total}>
          Confirmar Pago
        </Button>
      </CardFooter>
    </Card>
  )

  return (
    <div className="flex flex-col gap-4 p-4">
      {showPaymentConfirmation ? (
        <PaymentConfirmation />
      ) : (
        <div className="flex flex-col xl:flex-row gap-4">
          <Card className="w-full xl:w-1/3 xl:h-[calc(100vh-2rem)] flex flex-col">
            <CardHeader>
              <CardTitle>POS System</CardTitle>
            </CardHeader>
            <CardContent className="flex-grow overflow-auto">
              <div className="lg:mt-4">
                <Label>Carrito</Label>
                <ScrollArea className="h-[150px] lg:h-[200px] w-full rounded-md border p-4">
                  {cart.map((item) => (
                    <div key={item.id} className="flex justify-between items-center mb-2">
                      <span>{item.name}</span>
                      <div>
                        <Button variant="outline" size="sm" onClick={() => removeFromCart(item.id)}>
                          <Minus className="h-4 w-4" />
                        </Button>
                        <span className="mx-2">{item.quantity}</span>
                        <Button variant="outline" size="sm" onClick={() => addToCart(item)} disabled={inventory.find(p => p.id === item.id).stock === 0}>
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </ScrollArea>
              </div>
              <div>
                <Label htmlFor="discount">Descuento (%)</Label>
                <Input
                  id="discount"
                  type="number"
                  min="0"
                  max="100"
                  value={discount}
                  onChange={(e) => {
                    setDiscount(Math.min(100, Math.max(0, parseInt(e.target.value) || 0)))
                  }}
                  className="mb-2"
                />
              </div>
              <div className="text-right font-bold">
                Total: ${total.toFixed(2)}
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={handlePayment}>
                <CreditCard className="mr-2 h-4 w-4" /> Pagar
              </Button>
              <Button variant="outline" onClick={handleCancelSale}>
                <X className="mr-2 h-4 w-4" /> Cancelar Venta
              </Button>
            </CardFooter>
            {receipt && (
              <div className="mt-4 p-4 border-t">
                <h3 className="font-bold">Recibo:</h3>
                {receipt.items.map((item, index) => (
                  <div key={index}>{item.name} x{item.quantity}: ${(item.price * item.quantity).toFixed(2)}</div>
                ))}
                <div className="mt-2">Subtotal: ${receipt.subtotal.toFixed(2)}</div>
                <div>Descuento: {receipt.discount}%</div>
                <div className="font-bold">Total: ${receipt.total.toFixed(2)}</div>
                <div>Método de pago: {receipt.paymentMethod}</div>
                {receipt.paymentMethod === "efectivo" && (
                  <>
                    <div>Pagado: ${receipt.paid.toFixed(2)}</div>
                    <div>Cambio: ${receipt.change.toFixed(2)}</div>
                  </>
                )}
              </div>
            )}
          </Card>
          <div className="w-full xl:w-2/3 flex flex-col gap-4">
            <Card className="w-full flex-grow xl:h-[calc(50vh-1rem)] flex flex-col">
              <CardHeader>
                <CardTitle>Inventario</CardTitle>
              </CardHeader>
              <CardContent className="flex-grow overflow-auto">
                <div className="mb-4">
                  <Label htmlFor="search">Buscar Producto</Label>
                  <div className="flex items-center">
                    <Input
                      id="search"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      placeholder="Nombre del producto"
                      className="mr-2"
                    />
                    <Button variant="outline">
                      <Search className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nombre</TableHead>
                      <TableHead>Precio</TableHead>
                      <TableHead>Stock</TableHead>
                      <TableHead>Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredInventory.map(product => (
                      <TableRow key={product.id} className="cursor-pointer">
                        <TableCell onClick={() => setSelectedProduct(product)}>{product.name}</TableCell>
                        <TableCell onClick={() => setSelectedProduct(product)}>${product.price.toFixed(2)}</TableCell>
                        <TableCell onClick={() => setSelectedProduct(product)} className="flex items-center">
                          {product.stock}
                          {product.stock < 10 && (
                            <AlertTriangle className="h-4 w-4 ml-2 text-yellow-500" />
                          )}
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm" onClick={() => addToCart(product)} disabled={product.stock === 0}>
                            <Plus className="h-4 w-4" />
                            <span className="sr-only">Agregar al carrito</span>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
            <Card className="w-full flex-grow xl:h-[calc(50vh-1rem)] flex flex-col">
              <CardHeader>
                <CardTitle>Detalles del Producto</CardTitle>
              </CardHeader>
              <CardContent className="flex-grow overflow-auto">
                {selectedProduct ? (
                  <div className="flex flex-col items-center space-y-4">
                    <Image
                      src={selectedProduct.image}
                      alt={selectedProduct.name}
                      width={150}
                      height={150}
                      className="rounded-md w-[150px] h-[150px] lg:w-[200px] lg:h-[200px] object-cover"
                    />
                    <div className="text-center">
                      <h3 className="text-lg font-semibold">{selectedProduct.name}</h3>
                      <p className="text-sm text-gray-500">Precio: ${selectedProduct.price.toFixed(2)}</p>
                      <p className="text-sm text-gray-500">Stock: {selectedProduct.stock}</p>
                      <p className="mt-2">{selectedProduct.description}</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
                    <p>Selecciona un producto para ver sus detalles</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}