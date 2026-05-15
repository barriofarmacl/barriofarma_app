import React from 'react'
import { ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SECTION_IDS, HERO, assetBfSvg } from '@/lib/site-content'

export function LandingHero() {
  return (
    <section
      id={SECTION_IDS.hero}
      className="bg-purple-700 text-white py-16"
      aria-labelledby="landing-hero-title"
    >
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-2 gap-8 items-center">
          <div>
            <h1 id="landing-hero-title" className="text-4xl md:text-5xl font-bold mb-4">
              {HERO.title}
            </h1>
            <p className="text-lg mb-6 text-purple-100">{HERO.subtitle}</p>
            <Button variant="secondary" size="lg" asChild>
              <a href={HERO.ctaHref} className="flex items-center">
                {HERO.ctaLabel}
                <ChevronRight className="ml-2 h-4 w-4" aria-hidden />
              </a>
            </Button>
          </div>
          <div className="hidden md:flex justify-center">
            <img
              src={assetBfSvg}
              alt={HERO.imageAlt}
              className="rounded-lg w-full max-w-sm h-auto bg-white/10 p-8"
              width={320}
              height={320}
            />
          </div>
        </div>
      </div>
    </section>
  )
}
