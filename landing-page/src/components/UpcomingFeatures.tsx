'use client'

import { useEffect } from 'react'
import { staggerFadeIn } from '@/lib/animations'
import { Shield, FileCheck, Package, Users, Coins, Sparkles } from 'lucide-react'

export default function UpcomingFeatures() {
  useEffect(() => {
    staggerFadeIn('.upcoming-card', 0.15)
  }, [])

  const features = [
    {
      icon: Shield,
      title: 'HIPAA Compliance',
      description: 'Healthcare-grade data protection and audit trails for medical AI agents',
      status: 'Q2 2025',
      color: 'text-aop-indigo',
      bgColor: 'bg-aop-indigo/10',
      borderColor: 'border-aop-indigo/20',
    },
    {
      icon: FileCheck,
      title: 'GDPR Compliance',
      description: 'European privacy standards with right-to-deletion and consent tracking',
      status: 'Q2 2025',
      color: 'text-aop-purple',
      bgColor: 'bg-aop-purple/10',
      borderColor: 'border-aop-purple/20',
    },
    {
      icon: Package,
      title: 'AI Agentic Tool Call & MCP',
      description: 'Pre-built observability for AI agent tool calls and MCP server integration',
      status: 'v0.1.0 Alpha',
      color: 'text-aop-green',
      bgColor: 'bg-aop-green/10',
      borderColor: 'border-aop-green/20',
      badge: 'Available Now',
      badgeColor: 'bg-aop-green text-white',
    },
    {
      icon: Users,
      title: 'A2A Protocol',
      description: 'Agent-to-Agent communication tracking for multi-agent workflows',
      status: 'v0.1.0 Alpha',
      color: 'text-aop-turquoise',
      bgColor: 'bg-aop-turquoise/10',
      borderColor: 'border-aop-turquoise/20',
      badge: 'Available Now',
      badgeColor: 'bg-aop-turquoise text-white',
    },
    {
      icon: Coins,
      title: 'AP2 Protocol',
      description: 'Agent Payments Protocol for tracking costs and transactions',
      status: 'v0.1.0 Alpha',
      color: 'text-aop-gold',
      bgColor: 'bg-aop-gold/10',
      borderColor: 'border-aop-gold/20',
      badge: 'Available Now',
      badgeColor: 'bg-aop-gold text-white',
    },
    {
      icon: Sparkles,
      title: 'Coming Soon',
      description: 'Stream processing, batch optimization, and more storage backends',
      status: 'Roadmap',
      color: 'text-aop-beige',
      bgColor: 'bg-aop-beige/10',
      borderColor: 'border-aop-beige/20',
    },
  ]

  return (
    <section className="py-24 bg-aop-charcoal text-white">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            What's <span className="gradient-text">Next</span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Building the future of agent observability with compliance and enhanced protocols
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="upcoming-card opacity-0 group"
              >
                <div className={`bg-white/5 backdrop-blur-sm rounded-2xl p-6 border-2 ${feature.borderColor} hover:bg-white/10 transition-all duration-300 h-full flex flex-col relative overflow-hidden`}>
                  {/* Badge */}
                  {feature.badge && (
                    <div className="absolute top-4 right-4">
                      <span className={`text-xs font-bold px-3 py-1 rounded-full ${feature.badgeColor}`}>
                        {feature.badge}
                      </span>
                    </div>
                  )}

                  {/* Icon */}
                  <div className={`inline-flex items-center justify-center w-14 h-14 ${feature.bgColor} rounded-xl mb-4 group-hover:scale-110 transition-transform self-start`}>
                    <Icon className={`w-7 h-7 ${feature.color}`} />
                  </div>

                  {/* Title */}
                  <h3 className={`text-2xl font-bold ${feature.color} mb-3`}>
                    {feature.title}
                  </h3>

                  {/* Description */}
                  <p className="text-gray-300 mb-4 flex-1">
                    {feature.description}
                  </p>

                  {/* Status */}
                  <div className="flex items-center gap-2 text-sm">
                    <div className={`w-2 h-2 rounded-full ${feature.bgColor.replace('/10', '')}`} />
                    <span className="text-gray-400">{feature.status}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Roadmap CTA */}
        <div className="mt-16 text-center">
          <div className="inline-block bg-white/5 backdrop-blur-sm rounded-xl p-8 border border-aop-mint/20">
            <p className="text-lg text-gray-300 mb-4">
              Want to shape the roadmap? We're listening to the community.
            </p>
            <a
              href="https://github.com/aop-protocol/aop/discussions"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center px-6 py-3 bg-aop-mint text-aop-charcoal rounded-lg font-medium hover:bg-aop-green hover:text-white transition-colors"
            >
              Join the Discussion
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
