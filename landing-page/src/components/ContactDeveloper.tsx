'use client'

import { useEffect } from 'react'
import { fadeInUp, fadeInScale } from '@/lib/animations'
import { Mail, Linkedin, Github } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function ContactDeveloper() {
  useEffect(() => {
    fadeInScale('.contact-header', 0.2)
    fadeInUp('.contact-buttons', 0.4)
  }, [])

  const contacts = [
    {
      icon: Mail,
      label: 'Email',
      value: 'asing349@ucr.edu',
      href: 'mailto:asing349@ucr.edu',
      color: 'hover:bg-aop-red hover:border-aop-red',
      iconColor: 'text-aop-red',
    },
    {
      icon: Linkedin,
      label: 'LinkedIn',
      value: 'Connect on LinkedIn',
      href: 'https://linkedin.com/in/itsmeajit',
      color: 'hover:bg-aop-indigo hover:border-aop-indigo',
      iconColor: 'text-aop-indigo',
    },
    {
      icon: Github,
      label: 'GitHub',
      value: 'View on GitHub',
      href: 'https://github.com/asing349',
      color: 'hover:bg-aop-charcoal hover:border-aop-charcoal',
      iconColor: 'text-aop-charcoal',
    },
  ]

  return (
    <section id="contact" className="py-24 bg-gradient-to-br from-aop-beige/30 via-aop-gold/20 to-aop-beige/25">
      <div className="max-w-4xl mx-auto px-6">
        {/* Header */}
        <div className="contact-header text-center mb-12 opacity-0">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="text-aop-charcoal">Get in</span> <span className="gradient-text">Touch</span>
          </h2>
          <p className="text-xl text-aop-charcoal/90 max-w-2xl mx-auto">
            Questions, feedback, or collaboration? Reach out to the developer.
          </p>
        </div>

        {/* Developer Info */}
        <div className="text-center mb-8">
          <div className="inline-block bg-white rounded-2xl shadow-lg p-8 border-2 border-aop-mint/30">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-aop-green to-aop-turquoise flex items-center justify-center text-white text-3xl font-bold">
              AS
            </div>
            <h3 className="text-2xl font-bold text-aop-charcoal mb-2">
              Ajit Singh
            </h3>
            <p className="text-aop-gray mb-1">Creator & Maintainer</p>
            <p className="text-sm text-aop-gray">
              Building transparent AI systems
            </p>
          </div>
        </div>

        {/* Contact Buttons */}
        <div className="contact-buttons grid md:grid-cols-3 gap-4 opacity-0">
          {contacts.map((contact, index) => {
            const Icon = contact.icon
            return (
              <a
                key={index}
                href={contact.href}
                target={contact.href.startsWith('http') ? '_blank' : undefined}
                rel={contact.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                className={`group bg-white border-2 border-gray-200 rounded-xl p-6 flex flex-col items-center gap-3 transition-all duration-300 ${contact.color} hover:text-white hover:shadow-lg hover:scale-105`}
              >
                <Icon className={`w-8 h-8 ${contact.iconColor} group-hover:text-white transition-colors`} />
                <div className="text-center">
                  <p className="font-semibold text-sm text-aop-gray group-hover:text-white/80 mb-1">
                    {contact.label}
                  </p>
                  <p className="font-medium text-aop-charcoal group-hover:text-white">
                    {contact.value}
                  </p>
                </div>
              </a>
            )
          })}
        </div>

        {/* Additional Info */}
        <div className="mt-12 text-center">
          <p className="text-sm text-aop-gray">
            Open to collaborations, contributions, and feature requests
          </p>
        </div>
      </div>
    </section>
  )
}
