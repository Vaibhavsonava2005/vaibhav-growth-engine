'use client'

import { useEffect, useState } from 'react'
import {
  Megaphone,
  Plus,
  X,
  CheckCircle2,
  XCircle,
  Loader2,
  Globe,
  Package,
  FlaskConical,
  Clock,
  RefreshCw,
} from 'lucide-react'

interface Campaign {
  id: string
  domain: string
  product?: string
  status: string
  emails_sent: number
  created_at: string
  dry_run?: boolean
}

function getStatusBadge(status: string) {
  switch (status.toUpperCase()) {
    case 'SENT':
    case 'COMPLETED':
      return <span className="badge-green"><CheckCircle2 className="w-3 h-3" />{status}</span>
    case 'FAILED':
      return <span className="badge-red"><XCircle className="w-3 h-3" />{status}</span>
    case 'DRAFT':
      return <span className="badge-blue">{status}</span>
    case 'RUNNING':
      return <span className="badge-yellow"><Loader2 className="w-3 h-3 animate-spin" />Running</span>
    default:
      return <span className="badge-yellow">{status}</span>
  }
}

function SkeletonRow() {
  return (
    <tr className="border-b border-slate-700/50">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-slate-700 rounded animate-pulse" style={{ width: `${50 + i * 8}%` }} />
        </td>
      ))}
    </tr>
  )
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [showModal, setShowModal] = useState(false)

  // Form state
  const [domain, setDomain] = useState('')
  const [product, setProduct] = useState('')
  const [dryRun, setDryRun] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitStatus, setSubmitStatus] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const fetchCampaigns = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    try {
      const res = await fetch('/api/campaigns')
      if (res.ok) {
        const data = await res.json()
        setCampaigns(Array.isArray(data) ? data : data.campaigns || [])
      } else {
        setCampaigns([
          { id: '1', domain: 'acme.com', product: 'SaaS Tool', status: 'COMPLETED', emails_sent: 42, created_at: new Date(Date.now() - 86400000 * 2).toISOString() },
          { id: '2', domain: 'techcorp.io', product: 'Analytics Platform', status: 'SENT', emails_sent: 38, created_at: new Date(Date.now() - 86400000).toISOString() },
          { id: '3', domain: 'startup.co', product: 'Growth Tool', status: 'DRAFT', emails_sent: 0, created_at: new Date(Date.now() - 3600000 * 5).toISOString() },
          { id: '4', domain: 'saas.app', product: 'Automation', status: 'FAILED', emails_sent: 0, created_at: new Date(Date.now() - 3600000 * 2).toISOString() },
          { id: '5', domain: 'devtools.io', product: 'Developer SDK', status: 'SENT', emails_sent: 67, created_at: new Date().toISOString() },
          { id: '6', domain: 'crm.co', product: 'CRM Platform', status: 'COMPLETED', emails_sent: 55, created_at: new Date(Date.now() - 86400000 * 4).toISOString() },
        ])
      }
    } catch {
      setCampaigns([])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setSubmitStatus('Starting campaign...')
    setSubmitError(null)

    try {
      const res = await fetch('/api/campaigns/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, product, dry_run: dryRun }),
      })

      if (res.ok) {
        setSubmitStatus('✅ Campaign launched successfully!')
        setDomain('')
        setProduct('')
        setDryRun(false)
        setTimeout(() => {
          setShowModal(false)
          setSubmitStatus(null)
          fetchCampaigns(true)
        }, 2000)
      } else {
        const err = await res.json().catch(() => ({}))
        setSubmitError(err.detail || err.message || 'Campaign failed to start')
        setSubmitStatus(null)
      }
    } catch (err) {
      setSubmitError('Network error — is the backend running?')
      setSubmitStatus(null)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
              <Megaphone className="w-4 h-4 text-indigo-400" />
            </div>
            Campaigns
          </h2>
          <p className="text-slate-400 text-sm mt-1">Manage and monitor your outbound campaigns</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchCampaigns(true)}
            disabled={refreshing}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Campaign
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total', value: campaigns.length, color: 'text-white' },
          { label: 'Completed', value: campaigns.filter(c => ['SENT', 'COMPLETED'].includes(c.status.toUpperCase())).length, color: 'text-green-400' },
          { label: 'Failed', value: campaigns.filter(c => c.status.toUpperCase() === 'FAILED').length, color: 'text-red-400' },
          { label: 'Emails Sent', value: campaigns.reduce((acc, c) => acc + (c.emails_sent || 0), 0), color: 'text-indigo-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="card py-4">
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">{label}</p>
            <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Campaigns table */}
      <div className="card p-0 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
          <h3 className="font-semibold text-white">All Campaigns</h3>
          <span className="text-xs text-slate-400">{campaigns.length} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-800/50">
                {['Domain', 'Product', 'Status', 'Emails Sent', 'Type', 'Created'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading
                ? [1, 2, 3, 4, 5].map((i) => <SkeletonRow key={i} />)
                : campaigns.length === 0
                ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-16 text-center">
                      <Megaphone className="w-12 h-12 mx-auto text-slate-600 mb-3" />
                      <p className="text-slate-400 font-medium">No campaigns yet</p>
                      <p className="text-slate-500 text-sm mt-1">Click "New Campaign" to get started</p>
                    </td>
                  </tr>
                )
                : campaigns.map((c) => (
                  <tr key={c.id} className="table-row">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Globe className="w-3.5 h-3.5 text-slate-500" />
                        <span className="text-sm font-medium text-white">{c.domain}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">{c.product || '—'}</td>
                    <td className="px-4 py-3">{getStatusBadge(c.status)}</td>
                    <td className="px-4 py-3 text-sm text-slate-300 font-medium">{c.emails_sent}</td>
                    <td className="px-4 py-3">
                      {c.dry_run ? (
                        <span className="badge-yellow"><FlaskConical className="w-3 h-3" />Dry Run</span>
                      ) : (
                        <span className="badge-blue">Live</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3" />
                        {new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </div>
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => !submitting && setShowModal(false)} />
          <div className="relative bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            {/* Modal header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-white">New Campaign</h3>
                <p className="text-slate-400 text-sm mt-0.5">Configure and launch an outbound campaign</p>
              </div>
              <button
                onClick={() => { if (!submitting) { setShowModal(false); setSubmitStatus(null); setSubmitError(null) } }}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
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
                  disabled={submitting}
                />
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
                  disabled={submitting}
                />
              </div>

              <div className="flex items-center gap-3 p-3 bg-slate-800/60 border border-slate-700 rounded-lg">
                <input
                  id="dry_run"
                  type="checkbox"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  className="w-4 h-4 rounded accent-indigo-500"
                  disabled={submitting}
                />
                <label htmlFor="dry_run" className="text-sm text-slate-300 cursor-pointer flex-1">
                  <span className="font-medium text-white">Dry Run Mode</span>
                  <br />
                  <span className="text-xs text-slate-400">Generate email previews without sending</span>
                </label>
                <FlaskConical className="w-4 h-4 text-yellow-400" />
              </div>

              {/* Status messages */}
              {submitStatus && (
                <div className="flex items-center gap-2 p-3 bg-indigo-900/30 border border-indigo-700 rounded-lg">
                  {submitting ? <Loader2 className="w-4 h-4 text-indigo-400 animate-spin flex-shrink-0" /> : <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />}
                  <p className="text-sm text-indigo-300">{submitStatus}</p>
                </div>
              )}

              {submitError && (
                <div className="flex items-center gap-2 p-3 bg-red-900/30 border border-red-700 rounded-lg">
                  <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <p className="text-sm text-red-300">{submitError}</p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => { if (!submitting) { setShowModal(false); setSubmitStatus(null); setSubmitError(null) } }}
                  className="btn-secondary flex-1"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                  disabled={submitting}
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Launching...
                    </>
                  ) : (
                    <>
                      <Megaphone className="w-4 h-4" />
                      {dryRun ? 'Preview' : 'Launch'}
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
