import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SECTION_IDS, SERVICES } from '@/lib/site-content'

export function LandingServices() {
  return (
    <section id={SECTION_IDS.servicios} className="py-16" aria-labelledby="landing-svc-title">
      <div className="container mx-auto px-4">
        <h2 id="landing-svc-title" className="bf-heading-section mb-4">
          Servicios en sucursal
        </h2>
        <p className="text-center bf-text-muted max-w-2xl mx-auto mb-12">
          Trabajamos con atencion presencial. Si necesitas un producto, consulta en tienda o por los medios
          de contacto indicados abajo.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {SERVICES.map((service) => (
            <Card key={service.title}>
              <CardHeader>
                <CardTitle className="text-xl text-primary">{service.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="bf-text-muted">{service.body}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
