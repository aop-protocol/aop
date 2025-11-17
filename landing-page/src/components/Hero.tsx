'use client'

import { useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { cycleText, parallaxFloat, fadeInUp, fadeInScale } from '@/lib/animations'
import { Play, Github, Linkedin, Mail } from 'lucide-react'

export default function Hero() {
  const cycleRef = useRef<HTMLSpanElement>(null)
  const heroRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Cycling text animation
    if (cycleRef.current) {
      const words = ['TRANSPARENT', 'AUDITABLE', 'ACTIONABLE']
      let currentIndex = 0

      const cycle = () => {
        if (cycleRef.current) {
          cycleRef.current.textContent = words[currentIndex]
          currentIndex = (currentIndex + 1) % words.length
        }
      }

      // Initial set
      cycle()

      // Cycle every 3 seconds
      const interval = setInterval(cycle, 3000)

      return () => clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    // Entrance animations
    fadeInScale('.hero-logo', 0.2)
    fadeInUp('.hero-subtitle', 0.4)
    fadeInUp('.hero-tagline', 0.6)
    fadeInUp('.hero-cta', 0.8)
    fadeInUp('.hero-social', 1.0)

    // Parallax floating shapes
    parallaxFloat('.float-shape-1', 2, 30)
    parallaxFloat('.float-shape-2', 3, 40)
    parallaxFloat('.float-shape-3', 2.5, 35)
  }, [])

  return (
    <section
      ref={heroRef}
      className="relative min-h-screen bg-aop-charcoal text-white flex items-center justify-center overflow-hidden"
    >
      {/* Floating Background Shapes */}
      <div className="float-shape-1 absolute top-20 left-10 w-64 h-64 bg-aop-turquoise/10 rounded-full blur-3xl" />
      <div className="float-shape-2 absolute bottom-32 right-20 w-80 h-80 bg-aop-indigo/10 rounded-full blur-3xl" />
      <div className="float-shape-3 absolute top-1/2 right-1/3 w-72 h-72 bg-aop-purple/10 rounded-full blur-3xl" />

      {/* Content */}
      <div className="relative z-10 max-w-6xl mx-auto px-6 text-center">
        {/* Logo */}
        <h1 className="hero-logo text-9xl font-bold gradient-text mb-6 opacity-0">
          AOP
        </h1>

        {/* Subtitle */}
        <p className="hero-subtitle text-2xl text-aop-mint/80 mb-8 opacity-0">
          Agentic Observability Protocol
        </p>

        {/* Tagline with cycling text */}
        <p className="hero-tagline text-xl md:text-2xl text-gray-300 mb-12 max-w-4xl mx-auto opacity-0">
          Making MCP tools and AI agents behavior{' '}
          <span
            ref={cycleRef}
            className="gradient-text font-semibold inline-block min-w-[200px] text-left"
          >
            TRANSPARENT
          </span>
        </p>

        {/* CTA Buttons */}
        <div className="hero-cta flex flex-col sm:flex-row gap-4 justify-center items-center mb-12 opacity-0">
          <a href="https://github.com/aop-protocol/aop" target="_blank" rel="noopener noreferrer">
            <Button
              variant="gradient"
              size="lg"
              className="text-lg px-8 py-6 h-auto"
            >
              Get Started
            </Button>
          </a>
          <a href="#demo">
            <Button
              variant="outline"
              size="lg"
              className="text-lg px-8 py-6 h-auto"
            >
              <Play className="w-5 h-5 mr-2" />
              Watch Demo
            </Button>
          </a>
        </div>

        {/* Social Links */}
        <div className="hero-social flex gap-6 justify-center items-center opacity-0">
          <a
            href="mailto:asing349@ucr.edu"
            className="flex items-center gap-2 text-aop-mint/70 hover:text-aop-mint transition-colors group"
          >
            <Mail className="w-5 h-5 group-hover:scale-110 transition-transform" />
            <span className="text-sm">asing349@ucr.edu</span>
          </a>
          <span className="text-aop-mint/30">|</span>
          <a
            href="https://linkedin.com/in/ajitsingh"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-aop-mint/70 hover:text-aop-indigo transition-colors group"
          >
            <Linkedin className="w-5 h-5 group-hover:scale-110 transition-transform" />
            <span className="text-sm">LinkedIn</span>
          </a>
          <span className="text-aop-mint/30">|</span>
          <a
            href="https://github.com/aop-protocol/aop"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-aop-mint/70 hover:text-aop-turquoise transition-colors group"
          >
            <Github className="w-5 h-5 group-hover:scale-110 transition-transform" />
            <span className="text-sm">GitHub</span>
          </a>
        </div>
      </div>
    </section>
  )
}
