'use client'

import { useEffect, useState } from 'react'
import { scrollTriggerFade } from '@/lib/animations'
import { Play, CheckCircle, XCircle, Loader } from 'lucide-react'

export default function LiveDemo() {
  const [events, setEvents] = useState([
    {
      timestamp: '2025-01-16 10:23:45',
      agent: 'search-agent',
      type: 'mcp.tool.called',
      duration: '245ms',
      status: 'completed',
    },
    {
      timestamp: '2025-01-16 10:23:42',
      agent: 'orchestrator',
      type: 'a2a.task.assigned',
      duration: '12ms',
      status: 'completed',
    },
    {
      timestamp: '2025-01-16 10:23:40',
      agent: 'search-agent',
      type: 'mcp.sampling.request',
      duration: '1,234ms',
      status: 'completed',
    },
    {
      timestamp: '2025-01-16 10:23:38',
      agent: 'worker-agent',
      type: 'mcp.tool.called',
      duration: '89ms',
      status: 'error',
    },
    {
      timestamp: '2025-01-16 10:23:35',
      agent: 'payment-agent',
      type: 'ap2.payment.initiated',
      duration: '342ms',
      status: 'in_progress',
    },
  ])

  useEffect(() => {
    scrollTriggerFade('.live-demo-section', '.demo-item')

    // Simulate live updates every 5 seconds
    const interval = setInterval(() => {
      const newEvent = {
        timestamp: new Date().toLocaleString('en-US', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        }).replace(',', ''),
        agent: ['search-agent', 'orchestrator', 'worker-agent'][Math.floor(Math.random() * 3)],
        type: ['mcp.tool.called', 'a2a.task.assigned', 'mcp.sampling.request'][Math.floor(Math.random() * 3)],
        duration: `${Math.floor(Math.random() * 1000)}ms`,
        status: ['completed', 'error', 'in_progress'][Math.floor(Math.random() * 3)],
      }
      setEvents((prev) => [newEvent, ...prev.slice(0, 4)])
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-aop-green" />
      case 'error':
        return <XCircle className="w-5 h-5 text-aop-red" />
      case 'in_progress':
        return <Loader className="w-5 h-5 text-aop-indigo animate-spin" />
      default:
        return null
    }
  }

  return (
    <section id="demo" className="live-demo-section py-24 bg-aop-charcoal text-white">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            See It In <span className="gradient-text">Action</span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Real-time observability for every agent action, decision, and insight
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Left: Video */}
          <div className="demo-item opacity-0">
            <div className="relative aspect-video bg-gradient-to-br from-aop-indigo/10 to-aop-purple/10 rounded-2xl border-2 border-aop-turquoise/30 overflow-hidden flex items-center justify-center">
              <div className="text-center px-6">
                <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-aop-turquoise/20 to-aop-mint/20 rounded-full mb-6">
                  <Play className="w-12 h-12 text-aop-turquoise" />
                </div>
                <h3 className="text-3xl font-bold text-white mb-3">
                  Coming Soon
                </h3>
                <p className="text-aop-mint font-medium text-lg mb-2">Demo Video</p>
                <p className="text-sm text-gray-400 max-w-sm mx-auto">
                  Watch a complete walkthrough of AOP in action
                </p>
              </div>
            </div>

            {/* Video Caption */}
            <p className="text-center text-sm text-gray-400 mt-4">
              Installation → Integration → Real-time Insights
            </p>
          </div>

          {/* Right: Live Table */}
          <div className="demo-item opacity-0">
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl border border-aop-mint/20 overflow-hidden">
              {/* Table Header */}
              <div className="bg-aop-green/10 border-b border-aop-mint/20 px-6 py-4">
                <h3 className="text-lg font-semibold text-aop-mint flex items-center gap-2">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-aop-green opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-aop-green"></span>
                  </span>
                  Live Event Stream
                </h3>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-aop-mint/10 text-xs text-gray-400 uppercase">
                      <th className="px-4 py-3 text-left">Timestamp</th>
                      <th className="px-4 py-3 text-left">Agent</th>
                      <th className="px-4 py-3 text-left">Event</th>
                      <th className="px-4 py-3 text-right">Duration</th>
                      <th className="px-4 py-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((event, idx) => (
                      <tr
                        key={idx}
                        className="border-b border-aop-mint/5 hover:bg-white/5 transition-colors cursor-pointer group"
                      >
                        <td className="px-4 py-3 text-sm text-gray-300 font-mono">
                          {event.timestamp.split(' ')[1]}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className="text-aop-turquoise font-medium">
                            {event.agent}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-300">
                          {event.type}
                        </td>
                        <td className="px-4 py-3 text-sm text-right font-mono text-aop-gold">
                          {event.duration}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {getStatusIcon(event.status)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Footer */}
              <div className="bg-aop-charcoal/50 px-6 py-3 text-xs text-gray-400 flex items-center justify-between">
                <span>5 events shown · Updates every 5s</span>
                <span className="text-aop-turquoise">Click any row for details →</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
