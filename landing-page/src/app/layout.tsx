import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AOP - Agentic Observability Protocol',
  description: 'Making MCP tools and AI agents behavior Transparent, Auditable, and Actionable',
  keywords: 'AI agents, observability, MCP, A2A, AP2, agent monitoring, telemetry',
  authors: [{ name: 'Ajit Singh' }],
  openGraph: {
    title: 'AOP - Agentic Observability Protocol',
    description: 'Universal observability standard for AI agents',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
