'use client'

import { useEffect, useRef } from 'react'
import { horizontalScroll } from '@/lib/animations'
import { LayoutDashboard, GitBranch, LineChart, Terminal } from 'lucide-react'
import Image from 'next/image'

export default function FeaturesScroll() {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (containerRef.current) {
      const items = containerRef.current.querySelectorAll('.feature-card')
      horizontalScroll(containerRef.current, items)
    }
  }, [])

  const features = [
    {
      icon: LayoutDashboard,
      title: 'Dashboard Table View',
      description:
        'Professional tabular interface with sortable columns, live updates, and click-to-view details.',
      highlights: [
        'Sort by timestamp, agent, event type, or duration',
        'Color-coded status indicators',
        'Real-time WebSocket streaming',
        'Detailed JSON viewer on click',
      ],
      screenshot: '/screenshots/dashboard-table.png',
      color: 'from-aop-turquoise to-aop-indigo',
    },
    {
      icon: GitBranch,
      title: 'Trace Visualization',
      description:
        'Interactive tree view of distributed traces showing parent-child relationships across agents.',
      highlights: [
        'Complete trace reconstruction',
        'Correlation ID tracking',
        'Multi-agent workflow visualization',
        'Trace duration and event counts',
      ],
      screenshot: '/screenshots/trace-viz.png',
      color: 'from-aop-green to-aop-turquoise',
    },
    {
      icon: LineChart,
      title: 'Analytics Charts',
      description:
        'Real-time performance metrics, aggregations, and time-series analysis.',
      highlights: [
        'Tool usage statistics',
        'Latency percentiles (P95, P99)',
        'Event rate monitoring',
        'Time-bucketed timelines',
      ],
      screenshot: '/screenshots/analytics.png',
      color: 'from-aop-gold to-aop-purple',
    },
    {
      icon: Terminal,
      title: 'CLI Tools',
      description:
        'Powerful command-line interface for querying, exporting, and monitoring.',
      highlights: [
        'Query events with filters',
        'Export to JSON, CSV, OpenTelemetry',
        'Prometheus metrics server',
        'Interactive trace viewer',
      ],
      screenshot: '/screenshots/cli.png',
      color: 'from-aop-purple to-aop-red',
    },
  ]

  return (
    <section className="py-24 bg-gradient-to-br from-aop-red/15 via-aop-beige/25 to-aop-red/10 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 mb-12">
        <div className="text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="text-aop-charcoal">Powerful</span> <span className="gradient-text">Features</span>
          </h2>
          <p className="text-xl text-aop-charcoal/90 max-w-3xl mx-auto">
            Everything you need for complete observability
          </p>
        </div>
      </div>

      {/* Horizontal Scroll Container */}
      <div
        ref={containerRef}
        className="features-scroll-container relative"
        style={{ height: '600px' }}
      >
        <div className="flex gap-8 px-6">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="feature-card flex-shrink-0 w-[500px] group"
              >
                <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden hover:shadow-2xl transition-shadow h-full flex flex-col">
                  {/* Screenshot Placeholder */}
                  <div className={`relative h-64 bg-gradient-to-br ${feature.color} flex items-center justify-center overflow-hidden`}>
                    {/* Placeholder - replace with actual Image component when screenshots are ready */}
                    <div className="absolute inset-0 bg-aop-charcoal/10 flex items-center justify-center">
                      <Icon className="w-24 h-24 text-white/30" />
                    </div>
                    {/* Uncomment when screenshots are available:
                    <Image
                      src={feature.screenshot}
                      alt={feature.title}
                      fill
                      className="object-cover"
                    />
                    */}
                  </div>

                  {/* Content */}
                  <div className="p-6 flex-1 flex flex-col">
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`p-3 rounded-lg bg-gradient-to-br ${feature.color}`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-2xl font-bold text-aop-charcoal">
                        {feature.title}
                      </h3>
                    </div>

                    <p className="text-aop-gray mb-6">
                      {feature.description}
                    </p>

                    {/* Highlights */}
                    <ul className="space-y-2 flex-1">
                      {feature.highlights.map((highlight, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <span className="inline-block w-1.5 h-1.5 rounded-full bg-aop-green mt-1.5 flex-shrink-0" />
                          <span className="text-aop-charcoal">{highlight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-2 text-sm text-aop-gray">
          <span>Scroll to explore →</span>
        </div>
      </div>
    </section>
  )
}
