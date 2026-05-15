import React from 'react'
import {
  LandingHeader,
  LandingHero,
  LandingCategories,
  LandingServices,
  LandingContact,
  LandingFooter,
} from '@/components/landing'

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen">
      <LandingHeader />
      <main className="flex-1">
        <LandingHero />
        <LandingCategories />
        <LandingServices />
        <LandingContact />
      </main>
      <LandingFooter />
    </div>
  )
}
