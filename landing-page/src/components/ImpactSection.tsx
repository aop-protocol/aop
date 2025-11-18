'use client'

import { useEffect } from 'react'
import { scrollTriggerFade, fadeInUp } from '@/lib/animations'
import { Eye, FileCheck, BarChart3 } from 'lucide-react'

export default function ImpactSection() {
  useEffect(() => {
    scrollTriggerFade('.impact-section', '.impact-item')
  }, [])

  const impacts = [
    {
      icon: Eye,
      text: 'OBSERVE Every Action',
      color: 'text-green-700',
      bgColor: 'bg-green-700/10',
    },
    {
      icon: FileCheck,
      text: 'AUDIT Every Decision',
      color: 'text-aop-gold',
      bgColor: 'bg-aop-gold/10',
    },
    {
      icon: BarChart3,
      text: 'REPORT Every Insight',
      color: 'text-aop-purple',
      bgColor: 'bg-aop-purple/10',
    },
  ]

  return (
    <section className="impact-section py-24 bg-gradient-to-br from-aop-gold/25 via-aop-beige/30 to-aop-gold/20">
      <div className="max-w-7xl mx-auto px-6">
        {/* Main Bold Text */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-6xl font-bold leading-tight">
            <span className="gradient-text">Complete Visibility Into</span>
            <br />
            <span className="text-aop-charcoal">AI Agent Behavior</span>
          </h2>
        </div>

        {/* Impact Items */}
        <div className="grid md:grid-cols-3 gap-8">
          {impacts.map((item, index) => {
            const Icon = item.icon
            return (
              <div
                key={index}
                className="impact-item opacity-0 text-center group hover:scale-105 transition-transform duration-300"
              >
                {/* Icon */}
                <div
                  className={`inline-flex items-center justify-center w-20 h-20 ${item.bgColor} rounded-2xl mb-6 group-hover:shadow-lg transition-shadow`}
                >
                  <Icon className={`w-10 h-10 ${item.color}`} />
                </div>

                {/* Text */}
                <h3 className={`text-2xl font-bold ${item.color} mb-2`}>
                  {item.text.split(' ')[0]}
                </h3>
                <p className="text-xl text-aop-gray">
                  {item.text.split(' ').slice(1).join(' ')}
                </p>
              </div>
            )
          })}
        </div>

        {/* Separator */}
        <div className="mt-16 flex items-center justify-center gap-4">
          <div className="h-px w-24 bg-gradient-to-r from-transparent via-aop-turquoise to-transparent" />
          <span className="text-aop-turquoise text-xl">·</span>
          <div className="h-px w-24 bg-gradient-to-r from-transparent via-aop-gold to-transparent" />
          <span className="text-aop-gold text-xl">·</span>
          <div className="h-px w-24 bg-gradient-to-r from-transparent via-aop-purple to-transparent" />
        </div>
      </div>
    </section>
  )
}
