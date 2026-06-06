import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'
import {
  LayoutDashboard,
  Megaphone,
  Users,
  Mail,
  Activity,
  Download,
  Zap,
  Github,
  Menu,
} from 'lucide-react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Vaibhav Growth Engine',
  description: 'AI-powered outbound sales automation dashboard',
}

const navLinks = [
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/campaigns', label: 'Campaigns', icon: Megaphone },
  { href: '/leads', label: 'Leads', icon: Users },
  { href: '/email-preview', label: 'Email Preview', icon: Mail },
  { href: '/health', label: 'Health', icon: Activity },
  { href: '/export', label: 'Export', icon: Download },
]

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[#0f0f23] text-slate-200 min-h-screen`}>
        <div className="flex min-h-screen">
          {/* Sidebar - desktop */}
          <aside className="hidden lg:flex flex-col w-64 bg-slate-950 border-r border-slate-800 fixed inset-y-0 z-50">
            {/* Logo */}
            <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium tracking-wider uppercase">Vaibhav</p>
                <p className="text-sm font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  Growth Engine
                </p>
              </div>
            </div>

            {/* Nav links */}
            <nav className="flex-1 px-3 py-4 space-y-1">
              {navLinks.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all duration-150 group"
                >
                  <Icon className="w-4 h-4 group-hover:text-indigo-400 transition-colors" />
                  <span className="text-sm font-medium">{label}</span>
                </Link>
              ))}
            </nav>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-slate-800">
              <a
                href="https://github.com/Vaibhavsonava2005"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
              >
                <Github className="w-4 h-4" />
                <span>GitHub</span>
              </a>
              <p className="text-xs text-slate-600 mt-2">v1.0.0 • AI-Powered</p>
            </div>
          </aside>

          {/* Main content */}
          <div className="lg:ml-64 flex-1 flex flex-col min-h-screen">
            {/* Top header */}
            <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-4">
              <div className="flex items-center justify-between">
                {/* Mobile menu icon placeholder */}
                <div className="flex items-center gap-3 lg:hidden">
                  <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                    <Zap className="w-4 h-4 text-white" />
                  </div>
                  <span className="font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                    Growth Engine
                  </span>
                </div>

                {/* Desktop title */}
                <div className="hidden lg:block">
                  <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
                    Vaibhav Growth Engine
                  </h1>
                  <p className="text-xs text-slate-400">AI-Powered Outbound Sales Automation</p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-green-900/30 border border-green-800 rounded-full">
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                    <span className="text-xs text-green-400 font-medium">System Live</span>
                  </div>
                  <a
                    href="https://github.com/Vaibhavsonava2005"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-sm text-slate-300 transition-colors"
                  >
                    <Github className="w-4 h-4" />
                    <span>GitHub</span>
                  </a>
                </div>
              </div>

              {/* Mobile nav */}
              <nav className="flex lg:hidden gap-1 mt-3 overflow-x-auto pb-1">
                {navLinks.map(({ href, label, icon: Icon }) => (
                  <Link
                    key={href}
                    href={href}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all text-xs font-medium whitespace-nowrap"
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {label}
                  </Link>
                ))}
              </nav>
            </header>

            {/* Page content */}
            <main className="flex-1 px-4 lg:px-8 py-6">
              {children}
            </main>

            {/* Footer */}
            <footer className="border-t border-slate-800 px-8 py-4 text-center text-xs text-slate-600">
              © 2024 Vaibhav Growth Engine • Built with Next.js 14 + AI
            </footer>
          </div>
        </div>
      </body>
    </html>
  )
}
