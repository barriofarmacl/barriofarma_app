import React, { useState } from 'react'
import { Menu, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NAV_LINKS, SECTION_IDS, SITE } from '@/lib/site-content'

export function LandingHeader() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className="border-b bg-purple-800 relative">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <a href={`#${SECTION_IDS.hero}`} className="text-2xl font-bold text-white">
            {SITE.brand}
          </a>
          <button
            type="button"
            className="md:hidden text-white"
            onClick={() => setIsMenuOpen((o) => !o)}
            aria-label={isMenuOpen ? 'Cerrar menu' : 'Abrir menu'}
            aria-expanded={isMenuOpen}
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          <nav
            className={`${
              isMenuOpen ? 'flex' : 'hidden'
            } md:flex flex-col md:flex-row absolute md:relative top-full left-0 right-0 bg-purple-800 md:bg-transparent z-50 md:space-x-6 text-gray-100`}
            aria-label="Principal"
          >
            {NAV_LINKS.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="px-4 py-2 hover:bg-purple-700 md:hover:bg-transparent md:hover:text-white"
                onClick={() => setIsMenuOpen(false)}
              >
                {item.label}
              </a>
            ))}
            <Link
              to="/inicio/login"
              className="px-4 py-2 hover:bg-purple-700 md:hover:bg-transparent md:hover:text-white border-t border-purple-700 md:border-0"
              onClick={() => setIsMenuOpen(false)}
            >
              Acceso equipo
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}
