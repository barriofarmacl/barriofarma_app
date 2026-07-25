import React from 'react'
import { MapPin, Phone, Mail, Clock } from 'lucide-react'
import { SECTION_IDS, CONTACT } from '@/lib/site-content'

export function LandingContact() {
  return (
    <section id={SECTION_IDS.contacto} className="bf-section-muted py-16" aria-labelledby="landing-contact-title">
      <div className="container mx-auto px-4">
        <h2 id="landing-contact-title" className="bf-heading-section mb-12">
          Informacion de contacto
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bf-surface-card p-6 flex flex-col items-center text-center">
            <MapPin className="h-10 w-10 text-primary mb-4" aria-hidden />
            <h3 className="font-semibold mb-2">Direccion</h3>
            <p className="bf-text-muted">{CONTACT.addressLine}</p>
          </div>
          <div className="bf-surface-card p-6 flex flex-col items-center text-center">
            <Clock className="h-10 w-10 text-primary mb-4" aria-hidden />
            <h3 className="font-semibold mb-2">Horario</h3>
            {CONTACT.schedule.map((line) => (
              <p key={line} className="bf-text-muted">
                {line}
              </p>
            ))}
          </div>
          <div className="bf-surface-card p-6 flex flex-col items-center text-center">
            <Phone className="h-10 w-10 text-primary mb-4" aria-hidden />
            <h3 className="font-semibold mb-2">Telefono</h3>
            <p className="bf-text-muted">
              {CONTACT.phoneDisplay.includes('X') ? (
                <span>{CONTACT.phoneDisplay}</span>
              ) : (
                <a
                  className="underline hover:text-primary"
                  href={`tel:${CONTACT.phoneDisplay.replace(/[^\d+]/g, '')}`}
                >
                  {CONTACT.phoneDisplay}
                </a>
              )}
            </p>
            <p className="bf-text-muted mt-4 flex items-center gap-2">
              <Mail className="h-4 w-4 text-primary shrink-0" aria-hidden />
              <a className="underline hover:text-primary" href={`mailto:${CONTACT.email}`}>
                {CONTACT.email}
              </a>
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
