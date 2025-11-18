'use client'

import { Github, BookOpen, MessageCircle } from 'lucide-react'

export default function Footer() {
  const links = {
    product: [
      { label: 'Documentation', href: 'https://github.com/aop-protocol/aop/tree/main/docs' },
      { label: 'API Reference', href: 'https://github.com/aop-protocol/aop/blob/main/docs/api-reference.md' },
      { label: 'Examples', href: 'https://github.com/aop-protocol/aop/tree/main/examples' },
      { label: 'Roadmap', href: 'https://github.com/aop-protocol/aop/blob/main/RoadMap.md' },
    ],
    community: [
      { label: 'GitHub', href: 'https://github.com/aop-protocol/aop' },
      { label: 'Discussions', href: 'https://github.com/aop-protocol/aop/discussions' },
      { label: 'Issues', href: 'https://github.com/aop-protocol/aop/issues' },
      { label: 'Contributing', href: 'https://github.com/aop-protocol/aop/blob/main/CONTRIBUTING.md' },
    ],
    resources: [
      { label: 'Getting Started', href: 'https://github.com/aop-protocol/aop/blob/main/docs/getting-started.md' },
      { label: 'User Guide', href: 'https://github.com/aop-protocol/aop/blob/main/docs/user-guide.md' },
      { label: 'Troubleshooting', href: 'https://github.com/aop-protocol/aop/blob/main/docs/troubleshooting.md' },
      { label: 'Architecture', href: 'https://github.com/aop-protocol/aop/blob/main/docs/architecture.md' },
    ],
  }

  return (
    <footer className="bg-aop-charcoal text-white">
      <div className="max-w-7xl mx-auto px-6 py-16">
        {/* Top Section */}
        <div className="grid md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div>
            <h3 className="text-3xl font-bold gradient-text mb-3">AOP</h3>
            <p className="text-gray-400 text-sm mb-4">
              Agentic Observability Protocol
            </p>
            <p className="text-gray-500 text-xs">
              Making AI agents transparent, auditable, and actionable
            </p>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="font-semibold text-aop-mint mb-4">Product</h4>
            <ul className="space-y-2">
              {links.product.map((link, index) => (
                <li key={index}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-aop-turquoise transition-colors text-sm"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Community Links */}
          <div>
            <h4 className="font-semibold text-aop-mint mb-4">Community</h4>
            <ul className="space-y-2">
              {links.community.map((link, index) => (
                <li key={index}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-aop-turquoise transition-colors text-sm"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h4 className="font-semibold text-aop-mint mb-4">Resources</h4>
            <ul className="space-y-2">
              {links.resources.map((link, index) => (
                <li key={index}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-aop-turquoise transition-colors text-sm"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-gray-800 mb-8" />

        {/* Bottom Section */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          {/* Copyright */}
          <div className="text-gray-500 text-sm">
            © 2025 AOP Contributors. MIT License.
          </div>

          {/* Social Links */}
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/aop-protocol/aop"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-aop-turquoise transition-colors"
              aria-label="GitHub"
            >
              <Github className="w-5 h-5" />
            </a>
            <a
              href="https://github.com/aop-protocol/aop/tree/main/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-aop-turquoise transition-colors"
              aria-label="Documentation"
            >
              <BookOpen className="w-5 h-5" />
            </a>
            <a
              href="https://github.com/aop-protocol/aop/discussions"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-aop-turquoise transition-colors"
              aria-label="Discussions"
            >
              <MessageCircle className="w-5 h-5" />
            </a>
          </div>

          {/* Version Badge */}
          <div className="text-xs text-gray-500 bg-white/5 px-3 py-1 rounded-full">
            v0.1.0-alpha
          </div>
        </div>
      </div>
    </footer>
  )
}
