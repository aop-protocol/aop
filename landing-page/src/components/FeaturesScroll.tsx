'use client'

import { useEffect, useRef, useState } from 'react'
import { horizontalScroll } from '@/lib/animations'
import { LayoutDashboard, GitBranch, LineChart, Terminal } from 'lucide-react'
import Image from 'next/image'

export default function FeaturesScroll() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [scrollProgress, setScrollProgress] = useState(0)

  useEffect(() => {
    if (containerRef.current) {
      const items = containerRef.current.querySelectorAll('.feature-card')
      horizontalScroll(containerRef.current, items)
    }
  }, [])

  useEffect(() => {
    const handleScroll = () => {
      if (containerRef.current) {
        const container = containerRef.current.querySelector('.flex') as HTMLElement
        if (container) {
          const scrollLeft = container.scrollLeft
          const scrollWidth = container.scrollWidth - container.clientWidth
          const progress = (scrollLeft / scrollWidth) * 100
          setScrollProgress(progress)
        }
      }
    }

    const container = containerRef.current?.querySelector('.flex')
    if (container) {
      container.addEventListener('scroll', handleScroll)
      return () => container.removeEventListener('scroll', handleScroll)
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
      title: 'Trace Explorer - 3 Search Methods',
      description:
        'Interactive tree view of distributed traces with multiple search methods: Correlation ID, Event ID, or Parent ID.',
      highlights: [
        'Search by Correlation ID for planned workflows',
        'Search by Event ID - no correlation ID needed!',
        'Search by Parent ID for sub-operations',
        'Complete trace reconstruction with parent-child relationships',
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
      title: 'CLI & Export Tools',
      description:
        'Powerful command-line interface for querying, exporting to 5 formats, and monitoring.',
      highlights: [
        'Query events with rich filters',
        'Export to JSON, CSV, TOON (30-60% token savings)',
        'OpenTelemetry and Prometheus export',
        'Interactive trace viewer and analytics',
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

        {/* Scroll Progress Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2">
          <div className="w-48 h-1 bg-gray-300 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-aop-turquoise to-aop-purple transition-all duration-300"
              style={{ width: `${scrollProgress}%` }}
            />
          </div>
          <span className="text-sm text-aop-gray">Scroll</span>
        </div>
      </div>
    </section>
  )
}
