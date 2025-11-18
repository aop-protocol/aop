'use client'

import { useEffect } from 'react'
import Hero from '@/components/Hero'
import ImpactSection from '@/components/ImpactSection'
import MCPTabs from '@/components/MCPTabs'
import LiveDemo from '@/components/LiveDemo'
import FeaturesScroll from '@/components/FeaturesScroll'
import WhyAOP from '@/components/WhyAOP'
import UpcomingFeatures from '@/components/UpcomingFeatures'
import ContactDeveloper from '@/components/ContactDeveloper'
import Footer from '@/components/Footer'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

export default function Home() {
  useEffect(() => {
    // Register GSAP plugins
    gsap.registerPlugin(ScrollTrigger)

    // Smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth'

    return () => {
      // Cleanup
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill())
    }
  }, [])

  return (
    <main className="min-h-screen">
      <Hero />
      <ImpactSection />
      <MCPTabs />
      <LiveDemo />
      <FeaturesScroll />
      <WhyAOP />
      <UpcomingFeatures />
      <ContactDeveloper />
      <Footer />
    </main>
  )
}
