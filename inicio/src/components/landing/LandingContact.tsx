import React from 'react'
import { MapPin, Phone, Mail, Clock } from 'lucide-react'
import { SECTION_IDS, CONTACT } from '@/lib/site-content'

export function LandingContact() {
  return (
    <section id={SECTION_IDS.contacto} className="bg-gray-50 py-16" aria-labelledby="landing-contact-title">
      <div className="container mx-auto px-4">
        <h2 id="landing-contact-title" className="text-3xl font-bold text-center mb-12 text-purple-800">
          Informacion de contacto
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-md flex flex-col items-center text-center">
            <MapPin className="h-10 w-10 text-purple-700 mb-4" aria-hidden />
            <h3 className="font-semibold mb-2">Direccion</h3>
            <p className="text-gray-600">{CONTACT.addressLine}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md flex flex-col items-center text-center">
            <Clock className="h-10 w-10 text-purple-700 mb-4" aria-hidden />
            <h3 className="font-semibold mb-2">Horario</h3>
            {CONTACT.schedule.map((line) => (
              <p key={line} className="text-gray-600">
                {line}
              </p>
            ))}
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md flex flex-col items-center text-center">
            <Phone className="h-10 w-10 text-purple-700 mb-4" aria-hidden />
            <h3 className="font-semibold mb-2">Telefono</h3>
            <p className="text-gray-600">
              {CONTACT.phoneDisplay.includes('X') ? (
                <span>{CONTACT.phoneDisplay}</span>
              ) : (
                <a
                  className="underline hover:text-purple-800"
                  href={`tel:${CONTACT.phoneDisplay.replace(/[^\d+]/g, '')}`}
                >
                  {CONTACT.phoneDisplay}
                </a>
              )}
            </p>
            <p className="text-gray-600 mt-4 flex items-center gap-2">
              <Mail className="h-4 w-4 text-purple-700 shrink-0" aria-hidden />
              <a className="underline hover:text-purple-800" href={`mailto:${CONTACT.email}`}>
                {CONTACT.email}
              </a>
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
