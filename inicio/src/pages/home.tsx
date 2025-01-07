import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, MapPin, Phone, Mail, Clock, Menu, X } from 'lucide-react'

export default function HomePage() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b bg-purple-800 relative">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <a href="/" className="text-2xl font-bold text-white">
              Barriofarma
            </a>
            <button
              className="md:hidden text-white"
              onClick={toggleMenu}
              aria-label={isMenuOpen ? "Cerrar menú" : "Abrir menú"}
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <nav className={`${
              isMenuOpen ? 'flex' : 'hidden'
            } md:flex flex-col md:flex-row absolute md:relative top-full left-0 right-0 bg-purple-800 md:bg-transparent z-50 md:space-x-6 text-gray-100`}>
              <a href="#" className="px-4 py-2 hover:bg-purple-700 md:hover:bg-transparent md:hover:text-white">
                Inicio
              </a>
              <a href="/inicio/productos" className="px-4 py-2 hover:bg-purple-700 md:hover:bg-transparent md:hover:text-white">
                Productos
              </a>
              <a href="#" className="px-4 py-2 hover:bg-purple-700 md:hover:bg-transparent md:hover:text-white">
                Servicios
              </a>
              <a href="#" className="px-4 py-2 hover:bg-purple-700 md:hover:bg-transparent md:hover:text-white">
                Contacto
              </a>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="bg-purple-700 text-white py-16">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h1 className="text-4xl md:text-5xl font-bold mb-4">Tu salud es nuestra prioridad</h1>
                <p className="text-lg mb-6">
                  Encuentra todos los productos farmacéuticos que necesitas con el mejor servicio y asesoría profesional
                </p>
                <Link to="/inicio/productos">
                  <button className="bg-white text-purple-700 hover:bg-gray-100 px-6 py-2 rounded-md flex items-center">
                  Ver Productos
                  <ChevronRight className="ml-2 h-4 w-4" />
                  </button>
                </Link>
              </div>
              <div className="hidden md:block">
                <img
                  src="/placeholder.svg?height=400&width=400"
                  alt="Farmacia"
                  className="rounded-lg w-full h-auto"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Categories Section */}
        <section className="py-16 bg-gray-50">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12 text-purple-800">Nuestras Categorías</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { title: "Medicamentos", image: "medicine" },
                { title: "Dermocosméticos", image: "cosmetics" },
                { title: "Suplementos", image: "supplements" },
                { title: "Cuidado Personal", image: "personal-care" },
              ].map((category) => (
                <div key={category.title} className="bg-white p-4 sm:p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
                  <img
                    src={`/placeholder.svg?height=150&width=150`}
                    alt={category.title}
                    className="w-full max-w-[150px] h-auto mb-3 rounded-lg mx-auto"
                  />
                  <h3 className="text-base sm:text-lg font-semibold text-purple-800 text-center">{category.title}</h3>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Featured Products */}
        <section className="py-16">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12 text-purple-800">Productos Destacados</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map((product) => (
                <div key={product} className="bg-white p-4 rounded-lg shadow-md">
                  <img
                    src="/placeholder.svg?height=200&width=200"
                    alt={`Producto ${product}`}
                    className="w-full h-auto rounded-lg mb-4"
                  />
                  <h3 className="font-semibold text-purple-800">Producto {product}</h3>
                  <p className="text-gray-600">$9.990</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Contact Section */}
        <section className="bg-gray-50 py-16">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12 text-purple-800">Información de Contacto</h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-lg shadow-md flex flex-col items-center text-center">
                <MapPin className="h-10 w-10 text-purple-700 mb-4" />
                <h3 className="font-semibold mb-2">Dirección</h3>
                <p className="text-gray-600">Rojas Magallanes 94-B, La Florida Santiago</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md flex flex-col items-center text-center">
                <Clock className="h-10 w-10 text-purple-700 mb-4" />
                <h3 className="font-semibold mb-2">Horario</h3>
                <p className="text-gray-600">Lunes a Viernes: 10:00 - 19:00</p>
                <p className="text-gray-600">Sabados: 10:00 - 14:00</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md flex flex-col items-center text-center">
                <Phone className="h-10 w-10 text-purple-700 mb-4" />
                <h3 className="font-semibold mb-2">Teléfono</h3>
                <p className="text-gray-600">+56 9 11111111</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-purple-800 text-white py-8">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">Barriofarma</h3>
              <p className="text-gray-200">Tu farmacia de confianza en el barrio</p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4">Enlaces Rápidos</h3>
              <ul className="space-y-2">
                <li>
                  <a href="#" className="text-gray-200 hover:text-white">
                    Sobre Nosotros
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-200 hover:text-white">
                    Productos
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-200 hover:text-white">
                    Servicios
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4">Contacto</h3>
              <div className="space-y-2 text-gray-200">
                <p className="flex items-center">
                  <MapPin className="h-4 w-4 mr-2" />
                  Rojas Magallanes 94-B. La Florida
                </p>
                <p className="flex items-center">
                  <Phone className="h-4 w-4 mr-2" />
                  +56 9 11111111
                </p>
                <p className="flex items-center">
                  <Mail className="h-4 w-4 mr-2" />
                  contacto@barriofarma.cl
                </p>
              </div>
            </div>
          </div>
          <div className="border-t border-purple-700 mt-8 pt-8 text-center text-gray-200">
            <p>&copy; 2025 Barriofarma Dev. Todos los derechos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}