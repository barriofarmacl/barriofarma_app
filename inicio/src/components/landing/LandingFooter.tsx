import React from 'react'
import { MapPin, Phone, Mail } from 'lucide-react'
import { CONTACT, FOOTER_QUICK, SITE } from '@/lib/site-content'

export function LandingFooter() {
  return (
    <footer className="bg-purple-800 text-white py-8">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-lg font-semibold mb-4">{SITE.brand}</h3>
            <p className="text-gray-200">{SITE.tagline}</p>
            <p className="text-gray-300 text-sm mt-3">Sin venta online. Atencion en sucursal.</p>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4">Enlaces</h3>
            <ul className="space-y-2">
              {FOOTER_QUICK.map((item) => (
                <li key={item.href}>
                  <a href={item.href} className="text-gray-200 hover:text-white">
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4">Contacto</h3>
            <div className="space-y-2 text-gray-200">
              <p className="flex items-start">
                <MapPin className="h-4 w-4 mr-2 mt-1 shrink-0" aria-hidden />
                {CONTACT.addressShort}
              </p>
              <p className="flex items-center">
                <Phone className="h-4 w-4 mr-2 shrink-0" aria-hidden />
                {CONTACT.phoneDisplay.includes('X') ? (
                  <span>{CONTACT.phoneDisplay}</span>
                ) : (
                  <a
                    className="hover:text-white underline"
                    href={`tel:${CONTACT.phoneDisplay.replace(/[^\d+]/g, '')}`}
                  >
                    {CONTACT.phoneDisplay}
                  </a>
                )}
              </p>
              <p className="flex items-center">
                <Mail className="h-4 w-4 mr-2 shrink-0" aria-hidden />
                <a className="hover:text-white underline" href={`mailto:${CONTACT.email}`}>
                  {CONTACT.email}
                </a>
              </p>
            </div>
          </div>
        </div>
        <div className="border-t border-purple-700 mt-8 pt-8 text-center text-gray-200">
          <p>&copy; {new Date().getFullYear()} {SITE.brand}. Todos los derechos reservados.</p>
        </div>
      </div>
    </footer>
  )
}
