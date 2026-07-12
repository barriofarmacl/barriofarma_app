import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { SECTION_IDS, CATEGORIES, assetBfSvg } from '@/lib/site-content'

export function LandingCategories() {
  return (
    <section
      id={SECTION_IDS.categorias}
      className="py-16 bf-section-muted"
      aria-labelledby="landing-cat-title"
    >
      <div className="container mx-auto px-4">
        <h2 id="landing-cat-title" className="bf-heading-section mb-4">
          Categorias informativas
        </h2>
        <p className="text-center bf-text-muted max-w-2xl mx-auto mb-12">
          Referencia general de lineas que trabajamos en sucursal. Disponibilidad y marcas se confirman
          directamente en farmacia; esta web no es catalogo de venta.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
          {CATEGORIES.map((category) => (
            <Card key={category.title} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex justify-center mb-3">
                  <img
                    src={assetBfSvg}
                    alt=""
                    className="w-16 h-16 opacity-90"
                    width={64}
                    height={64}
                  />
                </div>
                <CardTitle className="text-lg text-primary text-center">{category.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center">{category.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
