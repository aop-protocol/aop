'use client'

import { useEffect, useRef } from 'react'
import { numberCounter, scrollTriggerFade } from '@/lib/animations'
import { Zap, Network, Shield, Package } from 'lucide-react'

export default function WhyAOP() {
  const sectionRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Animate counters when section comes into view
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            numberCounter('.stat-1', 0, 1, 1.5, '<', 'ms')
            numberCounter('.stat-2', 0, 3, 1.5)
            numberCounter('.stat-3', 0, 100, 1.5, '', '%')
            numberCounter('.stat-4', 0, 0, 1.5)
          }
        })
      },
      { threshold: 0.3 }
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    scrollTriggerFade('.why-aop-section', '.stat-card')

    return () => observer.disconnect()
  }, [])

  const stats = [
    {
      icon: Zap,
      value: '<1',
      suffix: 'ms',
      label: 'P99 Latency',
      description: 'Minimal overhead, production-ready performance',
      color: 'text-aop-gold',
      bgColor: 'bg-aop-gold/10',
      gradient: 'from-aop-gold to-aop-purple',
    },
    {
      icon: Network,
      value: '3',
      suffix: '',
      label: 'Protocols',
      description: 'MCP, A2A, and AP2 support out of the box',
      color: 'text-aop-turquoise',
      bgColor: 'bg-aop-turquoise/10',
      gradient: 'from-aop-turquoise to-aop-indigo',
    },
    {
      icon: Shield,
      value: '100',
      suffix: '%',
      label: 'Privacy',
      description: 'Local storage by default, you own your data',
      color: 'text-aop-green',
      bgColor: 'bg-aop-green/10',
      gradient: 'from-aop-green to-aop-turquoise',
    },
    {
      icon: Package,
      value: '0',
      suffix: '',
      label: 'Dependencies',
      description: 'Core library uses only Python stdlib',
      color: 'text-aop-purple',
      bgColor: 'bg-aop-purple/10',
      gradient: 'from-aop-purple to-aop-red',
    },
  ]

  return (
    <section
      ref={sectionRef}
      className="why-aop-section py-24 bg-gradient-to-br from-aop-green/20 via-aop-turquoise/30 to-aop-mint/35"
    >
      <div className="max-w-7xl mx-auto px-6">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="text-aop-charcoal">Why</span> <span className="gradient-text">AOP</span>?
          </h2>
          <p className="text-xl text-aop-charcoal/90 max-w-3xl mx-auto">
            Designed for production with privacy, performance, and simplicity in mind
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <div
                key={index}
                className="stat-card opacity-0 group"
              >
                <div className="bg-white rounded-2xl p-8 border-2 border-gray-100 hover:border-transparent hover:shadow-xl transition-all duration-300 h-full flex flex-col relative overflow-hidden">
                  {/* Gradient Border on Hover */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} opacity-0 group-hover:opacity-10 transition-opacity -z-10`} />

                  {/* Icon */}
                  <div className={`inline-flex items-center justify-center w-16 h-16 ${stat.bgColor} rounded-xl mb-6 group-hover:scale-110 transition-transform`}>
                    <Icon className={`w-8 h-8 ${stat.color}`} />
                  </div>

                  {/* Value */}
                  <div className="mb-2">
                    <span
                      className={`stat-${index + 1} text-5xl font-bold ${stat.color} inline-block`}
                    >
                      0
                    </span>
                    {stat.suffix && (
                      <span className={`text-3xl font-bold ${stat.color} ml-1`}>
                        {stat.suffix}
                      </span>
                    )}
                  </div>

                  {/* Label */}
                  <h3 className="text-xl font-bold text-aop-charcoal mb-3">
                    {stat.label}
                  </h3>

                  {/* Description */}
                  <p className="text-aop-gray text-sm flex-1">
                    {stat.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <p className="text-lg text-aop-gray mb-6">
            Join developers building transparent, auditable AI systems
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="https://github.com/aop-protocol/aop"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center px-8 py-3 bg-aop-charcoal text-white rounded-lg font-medium hover:bg-aop-charcoal/90 transition-colors"
            >
              View on GitHub
            </a>
            <a
              href="#contact"
              className="inline-flex items-center justify-center px-8 py-3 border-2 border-aop-turquoise text-aop-turquoise rounded-lg font-medium hover:bg-aop-turquoise hover:text-white transition-colors"
            >
              Get in Touch
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
