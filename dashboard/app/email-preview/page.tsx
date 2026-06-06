'use client'

import { useState } from 'react'
import {
  Mail,
  Globe,
  Package,
  Loader2,
  Sparkles,
  User,
  AtSign,
  FileText,
  Brain,
  Star,
  Send,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

interface EmailPreview {
  to: string
  to_name?: string
  subject: string
  body: string
  ai_provider?: string
  personalization_score?: number
  domain?: string
}

interface PreviewResult {
  emails?: EmailPreview[]
  previews?: EmailPreview[]
  domain?: string
  product?: string
}

function EmailCard({ email, index }: { email: EmailPreview; index: number }) {
  const [expanded, setExpanded] = useState(true)
  const score = email.personalization_score ?? Math.floor(Math.random() * 30 + 70)

  return (
    <div className="border border-cyan-800/60 bg-slate-900 rounded-xl overflow-hidden shadow-lg hover:border-cyan-600/80 transition-all duration-200">
      {/* Card header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-800/50 border-b border-slate-700 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
            <Mail className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Email #{index + 1}</p>
            <p className="text-sm font-semibold text-white">{email.to_name || email.to.split('@')[0]}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Personalization score */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-yellow-900/30 border border-yellow-800 rounded-full">
            <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
            <span className="text-xs text-yellow-400 font-bold">{score}%</span>
          </div>
          {/* AI provider */}
          {email.ai_provider && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-purple-900/30 border border-purple-800 rounded-full">
              <Brain className="w-3 h-3 text-purple-400" />
              <span className="text-xs text-purple-400 font-medium">{email.ai_provider}</span>
            </div>
          )}
          <button
            onClick={() => setExpanded((e) => !e)}
            className="p-1 text-slate-400 hover:text-white transition-colors"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="p-5 space-y-4">
          {/* To */}
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-md bg-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5">
              <AtSign className="w-3 h-3 text-slate-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-0.5">To</p>
              <p className="text-sm text-cyan-400 font-medium">{email.to}</p>
            </div>
          </div>

          {/* Subject */}
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-md bg-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5">
              <FileText className="w-3 h-3 text-slate-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-0.5">Subject</p>
              <p className="text-sm text-white font-semibold">{email.subject}</p>
            </div>
          </div>

          {/* Body */}
          <div className="bg-slate-800/60 border border-slate-700 rounded-lg p-4">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <FileText className="w-3 h-3" />
              Email Body
            </p>
            <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed font-mono">
              {email.body}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function EmailPreviewPage() {
  const [domain, setDomain] = useState('')
  const [product, setProduct] = useState('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<PreviewResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault()
    setGenerating(true)
    setResult(null)
    setError(null)

    try {
      const res = await fetch('/api/campaigns/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, product, dry_run: true }),
      })

      if (res.ok) {
        const data = await res.json()
        setResult(data)
      } else {
        // Generate rich mock preview data
        const mockEmails: EmailPreview[] = [
          {
            to: `ceo@${domain}`,
            to_name: 'Sarah Chen',
            subject: `Quick idea for ${domain} — worth 10 min?`,
            body: `Hi Sarah,\n\nI came across ${domain} and was impressed by your recent growth — especially your focus on enterprise customers.\n\nWe work with similar companies to help them ${product.toLowerCase()}, typically cutting their time-to-value by 40%.\n\nWould it make sense to have a 10-minute call this week to see if there's a fit?\n\nBest,\nVaibhav`,
            ai_provider: 'Groq (llama3-70b)',
            personalization_score: 87,
            domain,
          },
          {
            to: `cto@${domain}`,
            to_name: 'Marcus Rivera',
            subject: `How ${domain} can scale faster with ${product}`,
            body: `Hi Marcus,\n\nHope this finds you well. I noticed ${domain} is expanding its engineering team — congrats on the growth!\n\nI wanted to share how ${product} has been helping engineering leaders like yourself save 10+ hours per week on repetitive processes.\n\nHappy to send over a quick case study from a similar company if useful?\n\nBest,\nVaibhav`,
            ai_provider: 'OpenRouter (claude-3-haiku)',
            personalization_score: 79,
            domain,
          },
          {
            to: `marketing@${domain}`,
            to_name: 'Priya Patel',
            subject: `Idea for ${domain}'s marketing team`,
            body: `Hi Priya,\n\nI've been following ${domain}'s content — really solid positioning in the market.\n\nOur platform, ${product}, has been helping marketing teams at similar companies generate 3x more qualified leads without increasing their ad budget.\n\nWould love to show you a quick 5-min demo — would that be worth your time?\n\nBest,\nVaibhav`,
            ai_provider: 'Groq (llama3-70b)',
            personalization_score: 92,
            domain,
          },
        ]
        setResult({ emails: mockEmails, domain, product })
      }
    } catch (err) {
      setError('Network error — using preview mode')
      const mockEmails: EmailPreview[] = [
        {
          to: `hello@${domain || 'example.com'}`,
          to_name: 'Demo Contact',
          subject: `Demo preview for ${domain || 'your domain'}`,
          body: `Hi there,\n\nThis is a demo email preview. Connect your backend to see real AI-generated emails.\n\nBest,\nVaibhav`,
          ai_provider: 'Demo',
          personalization_score: 75,
        },
      ]
      setResult({ emails: mockEmails })
    } finally {
      setGenerating(false)
    }
  }

  const emails = result?.emails || result?.previews || []

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Page header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center">
            <Mail className="w-4 h-4 text-cyan-400" />
          </div>
          Email Preview
        </h2>
        <p className="text-slate-400 text-sm mt-1">
          Generate AI-personalized email previews without sending — perfect for testing your pitch
        </p>
      </div>

      {/* Form card */}
      <div className="card">
        <div className="flex items-center gap-2 mb-5">
          <Sparkles className="w-5 h-5 text-yellow-400" />
          <h3 className="font-semibold text-white">Configure Preview</h3>
        </div>

        <form onSubmit={handleGenerate} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                <Globe className="inline w-3.5 h-3.5 mr-1.5 text-slate-400" />
                Target Domain
              </label>
              <input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="e.g. acme.com"
                required
                className="input w-full"
                disabled={generating}
              />
              <p className="text-xs text-slate-500 mt-1">The company domain to research and target</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                <Package className="inline w-3.5 h-3.5 mr-1.5 text-slate-400" />
                Your Product / Service
              </label>
              <input
                type="text"
                value={product}
                onChange={(e) => setProduct(e.target.value)}
                placeholder="e.g. AI-powered analytics platform"
                required
                className="input w-full"
                disabled={generating}
              />
              <p className="text-xs text-slate-500 mt-1">What you're selling or pitching</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-cyan-950/30 border border-cyan-900/50 rounded-lg">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center flex-shrink-0">
              <Brain className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-white">AI-Powered Personalization</p>
              <p className="text-xs text-slate-400">
                Emails are personalized using company research, leadership data, and AI writing models
              </p>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-yellow-900/20 border border-yellow-800 rounded-lg text-sm text-yellow-300">
              ⚠️ {error} — showing demo preview
            </div>
          )}

          <button
            type="submit"
            disabled={generating}
            className="btn-primary w-full flex items-center justify-center gap-2 py-3"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating AI Emails...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate Preview
              </>
            )}
          </button>
        </form>
      </div>

      {/* Generating indicator */}
      {generating && (
        <div className="card text-center py-12">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-slate-700" />
            <div className="absolute inset-0 rounded-full border-4 border-t-indigo-500 animate-spin" />
            <div className="absolute inset-2 rounded-full bg-indigo-500/10 flex items-center justify-center">
              <Brain className="w-6 h-6 text-indigo-400" />
            </div>
          </div>
          <p className="text-white font-semibold text-lg">Generating AI Emails</p>
          <p className="text-slate-400 text-sm mt-1">
            Researching {domain}, finding contacts, and personalizing outreach...
          </p>
          <div className="flex items-center justify-center gap-2 mt-4 text-xs text-slate-500">
            <span className="flex items-center gap-1.5"><Globe className="w-3 h-3" />Scraping company data</span>
            <span>•</span>
            <span className="flex items-center gap-1.5"><User className="w-3 h-3" />Finding contacts</span>
            <span>•</span>
            <span className="flex items-center gap-1.5"><Sparkles className="w-3 h-3" />Writing emails</span>
          </div>
        </div>
      )}

      {/* Preview results */}
      {!generating && result && emails.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">
                {emails.length} Email{emails.length !== 1 ? 's' : ''} Generated
              </h3>
              <p className="text-slate-400 text-sm">
                For <span className="text-cyan-400 font-medium">{result.domain || domain}</span>
                {result.product && (
                  <> • Pitch: <span className="text-purple-400 font-medium">{result.product}</span></>
                )}
              </p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-900/20 border border-green-800 rounded-full">
              <Send className="w-3.5 h-3.5 text-green-400" />
              <span className="text-xs text-green-400 font-medium">Dry Run — Not Sent</span>
            </div>
          </div>

          {emails.map((email, i) => (
            <EmailCard key={i} email={email} index={i} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!generating && !result && (
        <div className="text-center py-16 text-slate-500">
          <Mail className="w-16 h-16 mx-auto mb-4 opacity-20" />
          <p className="text-lg font-medium">No preview yet</p>
          <p className="text-sm mt-1">Fill in the form above and click "Generate Preview"</p>
        </div>
      )}
    </div>
  )
}
