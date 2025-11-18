'use client'

import { useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { fadeInUp, fadeInScale } from '@/lib/animations'
import { Play, Github, Linkedin, Mail } from 'lucide-react'

export default function Hero() {
  const heroRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Entrance animations
    fadeInScale('.hero-logo', 0.2)
    fadeInUp('.hero-subtitle', 0.4)
    fadeInUp('.hero-tagline', 0.6)
    fadeInUp('.hero-cta', 0.8)
    fadeInUp('.hero-social', 1.0)
  }, [])

  return (
    <section
      ref={heroRef}
      className="relative min-h-screen bg-aop-charcoal text-white flex items-center justify-center overflow-hidden"
    >
      {/* Animated Grid Background */}
      <div className="absolute inset-0 opacity-10">
        {/* Vertical lines */}
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(90deg, rgba(58, 207, 105, 0.3) 1px, transparent 1px)`,
          backgroundSize: '80px 80px',
          animation: 'slideRight 30s linear infinite'
        }} />
        {/* Horizontal lines */}
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(0deg, rgba(107, 213, 201, 0.3) 1px, transparent 1px)`,
          backgroundSize: '80px 80px',
          animation: 'slideDown 30s linear infinite'
        }} />
      </div>

      {/* Floating particles */}
      <div className="absolute inset-0 opacity-30">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-aop-mint rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animation: `floatParticle ${15 + Math.random() * 10}s ease-in-out infinite`,
              animationDelay: `${Math.random() * 5}s`
            }}
          />
        ))}
      </div>

      {/* Gradient Orbs */}
      <div className="absolute top-20 left-10 w-96 h-96 bg-gradient-to-br from-aop-turquoise/20 to-aop-mint/10 rounded-full blur-3xl" style={{ animation: 'pulse 4s ease-in-out infinite' }} />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-gradient-to-br from-aop-indigo/20 to-aop-purple/10 rounded-full blur-3xl" style={{ animation: 'pulse 6s ease-in-out infinite' }} />

      {/* Content */}
      <div className="relative z-10 max-w-6xl mx-auto px-6 text-center">
        {/* Open Source Badge */}
        <div className="hero-logo flex items-center justify-center gap-3 mb-6 opacity-0">
          <div className="px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-aop-mint/30 flex items-center gap-2">
            <svg className="w-5 h-5 text-aop-mint" fill="currentColor" viewBox="0 0 16 16">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
            </svg>
            <span className="text-sm font-semibold text-aop-mint">Open Source</span>
          </div>
        </div>

        {/* Main Title */}
        <h1 className="hero-logo text-4xl md:text-6xl font-bold mb-4 opacity-0">
          <span className="text-white">Agentic Observability Protocol</span>
          <span className="text-3xl md:text-5xl text-gray-400 ml-3">(AOP)</span>
        </h1>

        {/* Tagline */}
        <p className="hero-subtitle text-2xl md:text-3xl text-aop-mint mb-8 opacity-0">
          Universal AI Agent Observability
        </p>

        {/* Supported Protocols */}
        <p className="hero-tagline text-lg md:text-xl text-gray-300 mb-12 max-w-4xl mx-auto opacity-0">
          Supports <span className="text-aop-turquoise font-semibold">MCP</span>, <span className="text-aop-gold font-semibold">A2A</span>, <span className="text-aop-purple font-semibold">AP2</span> and <span className="text-aop-green font-semibold">LangChain/LangGraph</span> agents
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
            href="https://linkedin.com/in/itsmeajit"
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
