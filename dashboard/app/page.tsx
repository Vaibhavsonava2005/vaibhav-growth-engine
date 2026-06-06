'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Megaphone,
  Mail,
  Users,
  Globe,
  TrendingUp,
  ArrowRight,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  BarChart3,
  RefreshCw,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface AnalyticsData {
  total_campaigns?: number
  emails_sent?: number
  contacts_found?: number
  domains_targeted?: number
  campaigns_by_status?: Record<string, number>
  emails_per_campaign?: Array<{ name: string; emails: number }>
}

interface HealthData {
  services?: Record<string, {
    status: string
    credits_remaining?: number
    plan?: string
    checked_at?: string
  }>
}

interface Campaign {
  id: string
  domain: string
  product?: string
  status: string
  emails_sent: number
  created_at: string
}

function SkeletonCard() {
  return (
    <div className="stat-card animate-pulse">
      <div className="h-4 bg-slate-700 rounded w-24" />
      <div className="h-8 bg-slate-700 rounded w-16 mt-1" />
      <div className="h-3 bg-slate-700 rounded w-32 mt-1" />
    </div>
  )
}

function SkeletonRow() {
  return (
    <tr className="border-b border-slate-700/50">
      {[1, 2, 3, 4, 5].map((i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-slate-700 rounded animate-pulse" style={{ width: `${60 + i * 10}%` }} />
        </td>
      ))}
    </tr>
  )
}

const SERVICE_INFO: Record<string, { label: string; color: string }> = {
  apollo: { label: 'Apollo.io', color: 'from-orange-500 to-orange-600' },
  hunter: { label: 'Hunter.io', color: 'from-yellow-500 to-yellow-600' },
  prospeo: { label: 'Prospeo', color: 'from-cyan-500 to-cyan-600' },
  brevo: { label: 'Brevo', color: 'from-blue-500 to-blue-600' },
  groq: { label: 'Groq AI', color: 'from-green-500 to-green-600' },
  openrouter: { label: 'OpenRouter', color: 'from-purple-500 to-purple-600' },
}

const CHART_COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#818cf8', '#4f46e5']

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 shadow-xl">
        <p className="text-slate-300 text-sm font-medium">{label}</p>
        <p className="text-indigo-400 text-lg font-bold">{payload[0].value} emails</p>
      </div>
    )
  }
  return null
}

export default function OverviewPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [health, setHealth] = useState<HealthData | null>(null)
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    try {
      const [analyticsRes, healthRes, campaignsRes] = await Promise.allSettled([
        fetch('/api/analytics'),
        fetch('/api/health'),
        fetch('/api/campaigns'),
      ])

      if (analyticsRes.status === 'fulfilled' && analyticsRes.value.ok) {
        const data = await analyticsRes.value.json()
        setAnalytics(data)
      } else {
        // Mock data for demonstration
        setAnalytics({
          total_campaigns: 12,
          emails_sent: 347,
          contacts_found: 892,
          domains_targeted: 45,
          emails_per_campaign: [
            { name: 'acme.com', emails: 42 },
            { name: 'techcorp.io', emails: 38 },
            { name: 'startup.co', emails: 55 },
            { name: 'saas.app', emails: 29 },
            { name: 'devtools.io', emails: 67 },
          ],
        })
      }

      if (healthRes.status === 'fulfilled' && healthRes.value.ok) {
        const data = await healthRes.value.json()
        setHealth(data)
      } else {
        setHealth({
          services: {
            apollo: { status: 'READY', credits_remaining: 450, plan: 'Pro' },
            hunter: { status: 'READY', credits_remaining: 190, plan: 'Starter' },
            prospeo: { status: 'NO KEY', credits_remaining: 0 },
            brevo: { status: 'READY', credits_remaining: 1200, plan: 'Free' },
            groq: { status: 'READY', plan: 'Free' },
            openrouter: { status: 'READY', credits_remaining: 85, plan: 'Pay-as-you-go' },
          },
        })
      }

      if (campaignsRes.status === 'fulfilled' && campaignsRes.value.ok) {
        const data = await campaignsRes.value.json()
        setCampaigns(Array.isArray(data) ? data.slice(0, 5) : data.campaigns?.slice(0, 5) || [])
      } else {
        setCampaigns([
          { id: '1', domain: 'acme.com', product: 'SaaS Tool', status: 'COMPLETED', emails_sent: 42, created_at: new Date(Date.now() - 86400000 * 2).toISOString() },
          { id: '2', domain: 'techcorp.io', product: 'Analytics Platform', status: 'SENT', emails_sent: 38, created_at: new Date(Date.now() - 86400000).toISOString() },
          { id: '3', domain: 'startup.co', product: 'Growth Tool', status: 'DRAFT', emails_sent: 0, created_at: new Date(Date.now() - 3600000 * 5).toISOString() },
          { id: '4', domain: 'saas.app', product: 'Automation', status: 'FAILED', emails_sent: 0, created_at: new Date(Date.now() - 3600000 * 2).toISOString() },
          { id: '5', domain: 'devtools.io', product: 'Developer SDK', status: 'SENT', emails_sent: 67, created_at: new Date().toISOString() },
        ])
      }
    } catch (err) {
      console.error('Failed to fetch data:', err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const statCards = [
    {
      label: 'Total Campaigns',
      value: analytics?.total_campaigns ?? '—',
      icon: Megaphone,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10',
      change: '+3 this week',
    },
    {
      label: 'Emails Sent',
      value: analytics?.emails_sent ?? '—',
      icon: Mail,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10',
      change: '+89 today',
    },
    {
      label: 'Contacts Found',
      value: analytics?.contacts_found ?? '—',
      icon: Users,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10',
      change: '+156 this week',
    },
    {
      label: 'Domains Targeted',
      value: analytics?.domains_targeted ?? '—',
      icon: Globe,
      color: 'text-green-400',
      bg: 'bg-green-500/10',
      change: '+12 this month',
    },
  ]

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'SENT':
      case 'COMPLETED':
        return <span className="badge-green"><CheckCircle2 className="w-3 h-3" />{status}</span>
      case 'FAILED':
        return <span className="badge-red"><XCircle className="w-3 h-3" />{status}</span>
      case 'DRAFT':
        return <span className="badge-blue">{status}</span>
      default:
        return <span className="badge-yellow">{status}</span>
    }
  }

  const chartData = analytics?.emails_per_campaign || []

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Dashboard Overview</h2>
          <p className="text-slate-400 text-sm mt-1">Real-time outbound campaign intelligence</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <Link href="/campaigns" className="btn-primary flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Run Campaign
          </Link>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {loading
          ? [1, 2, 3, 4].map((i) => <SkeletonCard key={i} />)
          : statCards.map(({ label, value, icon: Icon, color, bg, change }) => (
              <div key={label} className="stat-card card-hover">
                <div className="flex items-center justify-between">
                  <p className="text-slate-400 text-sm font-medium">{label}</p>
                  <div className={`w-9 h-9 rounded-lg ${bg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${color}`} />
                  </div>
                </div>
                <p className="text-3xl font-bold text-white">{value.toLocaleString?.() ?? value}</p>
                <p className="text-xs text-green-400 font-medium">{change}</p>
              </div>
            ))}
      </div>

      {/* Chart + Health grid */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        {/* Bar chart */}
        <div className="xl:col-span-3 card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-white">Emails per Campaign</h3>
              <p className="text-slate-400 text-sm">Recent campaign performance</p>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <BarChart3 className="w-4 h-4" />
              <span className="text-xs">Last 5 campaigns</span>
            </div>
          </div>
          {loading ? (
            <div className="h-52 bg-slate-800 rounded-lg animate-pulse" />
          ) : chartData.length === 0 ? (
            <div className="h-52 flex items-center justify-center text-slate-500">
              <div className="text-center">
                <BarChart3 className="w-10 h-10 mx-auto mb-2 opacity-30" />
                <p>No campaign data yet</p>
              </div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  axisLine={{ stroke: '#334155' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  axisLine={{ stroke: '#334155' }}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.1)' }} />
                <Bar dataKey="emails" radius={[4, 4, 0, 0]}>
                  {chartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Integration health */}
        <div className="xl:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Integration Health</h3>
            <Link href="/health" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-10 bg-slate-700 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {Object.entries(health?.services || {}).map(([key, svc]) => {
                const info = SERVICE_INFO[key] || { label: key, color: 'from-slate-500 to-slate-600' }
                const isReady = svc.status === 'READY'
                const hasError = svc.status === 'ERROR'
                return (
                  <div
                    key={key}
                    className="flex items-center justify-between p-2.5 bg-slate-800/60 rounded-lg border border-slate-700/50 hover:border-slate-600 transition-colors"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className={`w-7 h-7 rounded-md bg-gradient-to-br ${info.color} flex items-center justify-center text-white text-xs font-bold`}>
                        {info.label[0]}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{info.label}</p>
                        {svc.credits_remaining !== undefined && (
                          <p className="text-xs text-slate-400">{svc.credits_remaining} credits</p>
                        )}
                      </div>
                    </div>
                    <div
                      className={`w-2.5 h-2.5 rounded-full ${
                        isReady ? 'bg-green-400' : hasError ? 'bg-red-400' : 'bg-yellow-400'
                      }`}
                    />
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent campaigns table */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-white">Recent Campaigns</h3>
            <p className="text-slate-400 text-sm">Last 5 campaigns</p>
          </div>
          <Link href="/campaigns" className="btn-secondary flex items-center gap-2 text-sm">
            View all <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  {['Domain', 'Product', 'Status', 'Emails Sent', 'Created'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[1, 2, 3].map((i) => <SkeletonRow key={i} />)}
              </tbody>
            </table>
          </div>
        ) : campaigns.length === 0 ? (
          <div className="text-center py-12">
            <Megaphone className="w-12 h-12 mx-auto text-slate-600 mb-3" />
            <p className="text-slate-400 font-medium">No campaigns yet</p>
            <p className="text-slate-500 text-sm mt-1">Run your first campaign to get started</p>
            <Link href="/campaigns" className="btn-primary mt-4 inline-flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              New Campaign
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  {['Domain', 'Product', 'Status', 'Emails Sent', 'Created'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c) => (
                  <tr key={c.id} className="table-row">
                    <td className="px-4 py-3 text-sm font-medium text-white">{c.domain}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{c.product || '—'}</td>
                    <td className="px-4 py-3">{getStatusBadge(c.status)}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{c.emails_sent}</td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
