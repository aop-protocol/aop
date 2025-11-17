'use client'

import { useState, useEffect } from 'react'
import { scrollTriggerFade } from '@/lib/animations'
import { Book, Code2, FileCode, Zap } from 'lucide-react'

export default function MCPTabs() {
  const [activeTab, setActiveTab] = useState(0)

  useEffect(() => {
    scrollTriggerFade('.mcp-tabs-section', '.mcp-tab-content')
  }, [])

  const tabs = [
    {
      icon: Book,
      label: 'Documentation',
      content: {
        title: 'Complete MCP Documentation',
        description:
          'Comprehensive guides for integrating AOP with Model Context Protocol (MCP) tools and servers.',
        features: [
          'Tool execution observability with decorators',
          'LLM sampling request/response tracking',
          'Automatic parameter and result capture',
          'Error handling and exception tracking',
        ],
        codeExample: `@client.mcp.observe_tool(agent_id='my-agent')
def search_tool(query: str, max_results: int = 10):
    """Search for information."""
    results = perform_search(query, max_results)
    return {'results': results, 'count': len(results)}`,
      },
    },
    {
      icon: Code2,
      label: 'API Reference',
      content: {
        title: 'MCP Adapter API',
        description:
          'Full API reference for the MCP protocol adapter with type hints and examples.',
        features: [
          'observe_tool() decorator for automatic logging',
          'tool_execution() context manager',
          'log_sampling_request() for LLM calls',
          'log_sampling_response() for completions',
        ],
        codeExample: `# Context manager approach
with client.mcp.tool_execution(
    'my-agent',
    'search',
    {'query': 'AI agents'}
) as handle:
    result = search('AI agents')
    handle.set_result(result)`,
      },
    },
    {
      icon: FileCode,
      label: 'Examples',
      content: {
        title: 'Real-World Examples',
        description:
          'Production-ready examples showing MCP integration patterns with popular frameworks.',
        features: [
          'LangChain tool integration',
          'Async/await tool patterns',
          'Multi-step workflow tracking',
          'Distributed trace correlation',
        ],
        codeExample: `# LangChain Integration
from langchain.tools import Tool

@client.mcp.observe_tool(agent_id='langchain-agent')
def search_tool(query: str) -> str:
    return perform_search(query)

lc_tool = Tool(
    name="Search",
    func=search_tool,
    description="Search for information"
)`,
      },
    },
    {
      icon: Zap,
      label: 'Quick Start',
      content: {
        title: '5-Minute Quick Start',
        description:
          'Get up and running with MCP observability in minutes.',
        features: [
          'Install: pip install aop',
          'Add one-line decorator to your tools',
          'Query events with simple API',
          'View results in web dashboard',
        ],
        codeExample: `from aop import AOPClient

client = AOPClient()

@client.mcp.observe_tool(agent_id='my-agent')
def my_tool(param: str):
    return process(param)

# That's it! Everything is logged automatically.`,
      },
    },
  ]

  return (
    <section className="mcp-tabs-section py-24 bg-gradient-to-br from-aop-indigo/20 via-aop-purple/25 to-aop-indigo/15">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="gradient-text">MCP Integration</span> <span className="text-aop-charcoal">Hub</span>
          </h2>
          <p className="text-xl text-aop-charcoal/90 max-w-3xl mx-auto">
            Everything you need to add observability to Model Context Protocol tools
          </p>
        </div>

        {/* Tabs Navigation */}
        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {tabs.map((tab, index) => {
            const Icon = tab.icon
            return (
              <button
                key={index}
                onClick={() => setActiveTab(index)}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
                  activeTab === index
                    ? 'bg-aop-green text-white shadow-lg scale-105'
                    : 'bg-white text-aop-charcoal hover:bg-aop-mint/20 border border-aop-mint'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Tab Content */}
        <div className="mcp-tab-content bg-white rounded-2xl shadow-xl p-8 md:p-12 border border-aop-mint/20 opacity-0">
          <div className="grid md:grid-cols-2 gap-12 items-start">
            {/* Left: Description */}
            <div>
              <h3 className="text-3xl font-bold text-aop-charcoal mb-4">
                {tabs[activeTab].content.title}
              </h3>
              <p className="text-lg text-aop-gray mb-6">
                {tabs[activeTab].content.description}
              </p>

              {/* Features List */}
              <ul className="space-y-3">
                {tabs[activeTab].content.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <span className="inline-block w-6 h-6 rounded-full bg-aop-green/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="w-2 h-2 rounded-full bg-aop-green" />
                    </span>
                    <span className="text-aop-charcoal">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Right: Code Example */}
            <div className="relative">
              <div className="absolute -top-3 -left-3 w-full h-full bg-gradient-to-br from-aop-turquoise/20 to-aop-purple/20 rounded-xl -z-10" />
              <pre className="bg-aop-charcoal text-white p-6 rounded-xl overflow-x-auto text-sm">
                <code>{tabs[activeTab].content.codeExample}</code>
              </pre>
              <div className="absolute top-4 right-4 flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-aop-red/60" />
                <div className="w-3 h-3 rounded-full bg-aop-gold/60" />
                <div className="w-3 h-3 rounded-full bg-aop-green/60" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
