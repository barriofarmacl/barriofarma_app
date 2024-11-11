import React, { useState, useEffect } from 'react'

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

  const updateTotal = () => {
    const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
    const discountAmount = subtotal * (discount / 100)
    setTotal(subtotal - discountAmount)
  }

  const addToCart = (product) => {
    if (product.stock > 0) {
      setCart(prevCart => {
        const existingItem = prevCart.find(item => item.id === product.id)
        if (existingItem) {
          return prevCart.map(item =>
            item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
          )
        } else {
          return [...prevCart, { ...product, quantity: 1 }]
        }
      })
      setInventory(prevInventory =>
        prevInventory.map(item =>
          item.id === product.id ? { ...item, stock: item.stock - 1 } : item
        )
      )
    } else {
      alert("No hay stock disponible para este producto.")
    }
  }

  const removeFromCart = (productId) => {
    setCart(prevCart => {
      const updatedCart = prevCart.map(item =>
        item.id === productId ? { ...item, quantity: item.quantity - 1 } : item
      ).filter(item => item.quantity > 0)
      return updatedCart
    })
    setInventory(prevInventory =>
      prevInventory.map(item =>
        item.id === productId ? { ...item, stock: item.stock + 1 } : item
      )
    )
  }

  const handlePayment = () => {
    if (cart.length === 0) {
      alert("El carrito está vacío. Agregue productos antes de proceder al pago.")
      return
    }
    setShowPaymentConfirmation(true)
  }

  const handleConfirmPayment = () => {
    if (paymentMethod === "efectivo" && parseFloat(amountReceived) < total) {
      alert("El monto recibido es insuficiente.")
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
    alert("Venta completada")
  }

  const handleCancelSale = () => {
    setInventory(prevInventory => {
      const updatedInventory = [...prevInventory]
      cart.forEach(cartItem => {
        const inventoryItem = updatedInventory.find(item => item.id === cartItem.id)
        if (inventoryItem) {
          inventoryItem.stock += cartItem.quantity
        }
      })
      return updatedInventory
    })
    setCart([])
    setTotal(0)
    setShowPaymentConfirmation(false)
    setDiscount(0)
    alert("Venta cancelada")
  }

  const filteredInventory = inventory
    .filter(product => product.name.toLowerCase().includes(searchTerm.toLowerCase()))
    .slice(0, 5)

  const PaymentConfirmation = () => (
    <div className="w-full max-w-md mx-auto bg-gray-100 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 text-purple-800">Confirmar Pago</h2>
      <div className="h-[200px] overflow-y-auto border rounded-md p-4 mb-4 bg-white">
        <table className="w-full">
          <thead>
            <tr>
              <th className="text-left">Producto</th>
              <th className="text-left">Cantidad</th>
              <th className="text-left">Precio</th>
            </tr>
          </thead>
          <tbody>
            {cart.map((item) => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{item.quantity}</td>
                <td>${(item.price * item.quantity).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="text-right mb-4">
        <div>Subtotal: ${cart.reduce((sum, item) => sum + item.price * item.quantity, 0).toFixed(2)}</div>
        <div>Descuento: {discount}%</div>
        <div className="font-bold">Total: ${total.toFixed(2)}</div>
      </div>
      <div className="mb-4">
        <label className="block mb-2">Método de pago:</label>
        <div className="flex space-x-4">
          <label className="flex items-center">
            <input
              type="radio"
              value="efectivo"
              checked={paymentMethod === "efectivo"}
              onChange={() => setPaymentMethod("efectivo")}
              className="mr-2"
            />
            Efectivo
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="tarjeta"
              checked={paymentMethod === "tarjeta"}
              onChange={() => setPaymentMethod("tarjeta")}
              className="mr-2"
            />
            Tarjeta
          </label>
        </div>
      </div>
      {paymentMethod === "efectivo" && (
        <div className="mb-4">
          <label htmlFor="amountReceived" className="block mb-2">Monto Recibido:</label>
          <input
            id="amountReceived"
            type="number"
            value={amountReceived}
            onChange={(e) => setAmountReceived(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-700"
          />
          {parseFloat(amountReceived) >= total && (
            <div className="mt-2 text-right">
              Cambio: ${(parseFloat(amountReceived) - total).toFixed(2)}
            </div>
          )}
        </div>
      )}
      <div className="flex justify-between">
        <button
          onClick={() => setShowPaymentConfirmation(false)}
          className="px-4 py-2 bg-gray-400 text-white rounded-md hover:bg-gray-500 transition-colors"
        >
          <i className="fas fa-arrow-left mr-2"></i> Volver
        </button>
        <button
          onClick={handleConfirmPayment}
          disabled={paymentMethod === "efectivo" && parseFloat(amountReceived) < total}
          className="px-4 py-2 bg-purple-700 text-white rounded-md hover:bg-purple-800 transition-colors disabled:bg-gray-400"
        >
          Confirmar Pago
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex flex-col gap-4 p-4 bg-white min-h-screen">
      {showPaymentConfirmation ? (
        <PaymentConfirmation />
      ) : (
        <div className="flex flex-col xl:flex-row gap-4">
          <div className="w-full xl:w-1/3 xl:h-[calc(100vh-2rem)] flex flex-col bg-gray-100 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold p-4 bg-purple-700 text-white rounded-t-lg">POS System</h3>
            <div className="flex-grow overflow-auto p-4">
              <div className="mb-4">
                <p className="mb-2 font-semibold text-purple-800">Carrito</p>
                <div className="h-[200px] overflow-y-auto border rounded-md p-2 bg-white">
                  {cart.map((item) => (
                    <div key={item.id} className="flex justify-between items-center mb-2">
                      <span>{item.name}</span>
                      <div>
                        <button onClick={() => removeFromCart(item.id)} className="px-2 py-1 bg-purple-700 text-white rounded-md hover:bg-purple-800 transition-colors">
                          <i className="fas fa-minus"></i>
                        </button>
                        <span className="mx-2">{item.quantity}</span>
                        <button onClick={() => addToCart(item)} disabled={inventory.find(p => p.id === item.id).stock === 0} className="px-2 py-1 bg-purple-700 text-white rounded-md hover:bg-purple-800 transition-colors disabled:bg-gray-400">
                          <i className="fas fa-plus"></i>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mb-4">
                <label htmlFor="discount" className="block mb-1 font-semibold text-purple-800">Descuento (%)</label>
                <input
                  id="discount"
                  type="number"
                  min="0"
                  max="100"
                  value={discount}
                  onChange={(e) => setDiscount(Math.min(100, Math.max(0, parseInt(e.target.value) || 0)))}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-700"
                />
              </div>
              <div className="text-right font-bold text-purple-800">
                Total: ${total.toFixed(2)}
              </div>
            </div>
            <div className="flex justify-between p-4 bg-gray-200 rounded-b-lg">
              <button onClick={handlePayment} className="px-4 py-2 bg-purple-700 text-white rounded-md hover:bg-purple-800 transition-colors">
                <i className="fas fa-credit-card mr-2"></i> Pagar
              </button>
              <button onClick={handleCancelSale} className="px-4 py-2 bg-gray-400 text-white rounded-md hover:bg-gray-500 transition-colors">
                <i className="fas fa-times mr-2"></i> Cancelar Venta
              </button>
            </div>
            {receipt && (
              <div className="mt-4 p-4 border-t border-gray-300">
                <h3 className="font-bold text-purple-800">Recibo:</h3>
                {receipt.items.map((item, index) => (
                  <div key={index}>
                    {item.name} x{item.quantity}: ${(item.price * item.quantity).toFixed(2)}
                  </div>
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
          </div>
          <div className="w-full xl:w-2/3 flex flex-col gap-4">
            <div className="w-full flex-grow xl:h-[calc(50vh-1rem)] flex flex-col bg-gray-100 rounded-lg shadow-md">
              <h3 className="text-xl font-semibold p-4 bg-purple-700 text-white rounded-t-lg">Inventario</h3>
              <div className="flex-grow overflow-auto p-4">
                <div className="mb-4">
                  <label htmlFor="search" className="block mb-1 font-semibold text-purple-800">Buscar Producto</label>
                  <div className="flex items-center">
                    <input
                      id="search"
                      type="text"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      placeholder="Nombre del producto"
                      className="flex-grow px-3 py-2 border rounded-l-md focus:outline-none focus:ring-2 focus:ring-purple-700"
                    />
                    <button className="px-4 py-2 bg-purple-700 text-white rounded-r-md hover:bg-purple-800 transition-colors">
                      <i className="fas fa-search"></i>
                    </button>
                  </div>
                </div>
                <table className="w-full bg-white">
                  <thead className="bg-purple-700 text-white">
                    <tr>
                      <th className="p-2 text-left">Nombre</th>
                      <th className="p-2 text-left">Precio</th>
                      <th className="p-2 text-left">Stock</th>
                      <th className="p-2 text-left">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredInventory.map(product => (
                      <tr key={product.id} className="border-b border-gray-200 hover:bg-gray-50">
                        <td className="p-2" onClick={() => setSelectedProduct(product)}>{product.name}</td>
                        <td className="p-2" onClick={() => setSelectedProduct(product)}>${product.price.toFixed(2)}</td>
                        <td className="p-2" onClick={() => setSelectedProduct(product)}>
                          {product.stock}
                          {product.stock < 10 && (
                            <i className="fas fa-exclamation-triangle text-yellow-500 ml-2"></i>
                          )}
                        </td>
                        <td className="p-2">
                          <button onClick={() => addToCart(product)} disabled={product.stock === 0} className="px-2 py-1 bg-purple-700 text-white rounded-md hover:bg-purple-800 transition-colors disabled:bg-gray-400">
                            <i className="fas fa-plus"></i>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="w-full flex-grow xl:h-[calc(50vh-1rem)] flex flex-col bg-gray-100 rounded-lg shadow-md">
              <h3 className="text-xl font-semibold p-4 bg-purple-700 text-white rounded-t-lg">Detalles del Producto</h3>
              <div className="flex-grow overflow-auto p-4">
                {selectedProduct ? (
                  <div className="flex flex-col xl:flex-row items-center xl:items-start space-y-4 xl:space-y-0 xl:space-x-4">
                    <div className="w-full xl:w-1/2 order-2 xl:order-1">
                      <div className="text-center xl:text-left">
                        <h3 className="text-lg font-semibold text-purple-800">{selectedProduct.name}</h3>
                        <p className="text-sm text-gray-600">Precio: ${selectedProduct.price.toFixed(2)}</p>
                        <p className="text-sm text-gray-600">Stock: {selectedProduct.stock}</p>
                        <p className="mt-2 text-gray-700">{selectedProduct.description}</p>
                      </div>
                    </div>
                    <div className="w-full xl:w-1/2 flex justify-center xl:justify-end order-1 xl:order-2">
                      <img
                        src={selectedProduct.image}
                        alt={selectedProduct.name}
                        className="rounded-md w-[150px] h-[150px] lg:w-[200px] lg:h-[200px] object-cover"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
                    <p>Selecciona un producto para ver sus detalles</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}