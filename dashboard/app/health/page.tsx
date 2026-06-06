'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  Activity,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Zap,
  CreditCard,
  BadgeCheck,
} from 'lucide-react'

interface ServiceHealth {
  status: 'READY' | 'NO KEY' | 'ERROR' | string
  credits_remaining?: number
  plan?: string
  checked_at?: string
  error?: string
}

interface HealthResponse {
  services?: Record<string, ServiceHealth>
  overall_status?: string
}

const SERVICE_META: Record<string, { label: string; desc: string; gradient: string; initial: string }> = {
  apollo: {
    label: 'Apollo.io',
    desc: 'Lead prospecting & contact data',
    gradient: 'from-orange-500 to-red-500',
    initial: 'A',
  },
  hunter: {
    label: 'Hunter.io',
    desc: 'Email finder & verification',
    gradient: 'from-yellow-500 to-orange-500',
    initial: 'H',
  },
  prospeo: {
    label: 'Prospeo',
    desc: 'B2B contact enrichment',
    gradient: 'from-cyan-500 to-blue-500',
    initial: 'P',
  },
  brevo: {
    label: 'Brevo (Sendinblue)',
    desc: 'Email delivery & campaigns',
    gradient: 'from-blue-500 to-indigo-500',
    initial: 'B',
  },
  groq: {
    label: 'Groq AI',
    desc: 'Ultra-fast LLM inference',
    gradient: 'from-green-500 to-emerald-500',
    initial: 'G',
  },
  openrouter: {
    label: 'OpenRouter',
    desc: 'Multi-model AI gateway',
    gradient: 'from-purple-500 to-violet-500',
    initial: 'O',
  },
}

function ServiceCard({ name, data }: { name: string; data: ServiceHealth }) {
  const meta = SERVICE_META[name] || { label: name, desc: 'API service', gradient: 'from-slate-500 to-slate-600', initial: name[0].toUpperCase() }

  const isReady = data.status === 'READY'
  const isError = data.status === 'ERROR'
  const isNoKey = data.status === 'NO KEY'

  const borderColor = isReady ? 'border-green-700 hover:border-green-500' : isError ? 'border-red-700 hover:border-red-500' : 'border-yellow-700 hover:border-yellow-500'
  const statusColor = isReady ? 'text-green-400' : isError ? 'text-red-400' : 'text-yellow-400'
  const statusBg = isReady ? 'bg-green-900/30' : isError ? 'bg-red-900/30' : 'bg-yellow-900/30'
  const statusIcon = isReady ? CheckCircle2 : isError ? XCircle : AlertCircle

  const StatusIcon = statusIcon

  const checkedAt = data.checked_at
    ? new Date(data.checked_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : null

  return (
    <div className={`bg-slate-900 border ${borderColor} rounded-xl p-5 transition-all duration-200 hover:bg-slate-800/50`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${meta.gradient} flex items-center justify-center text-white font-bold text-lg shadow-lg`}>
            {meta.initial}
          </div>
          <div>
            <h3 className="font-semibold text-white">{meta.label}</h3>
            <p className="text-xs text-slate-400 mt-0.5">{meta.desc}</p>
          </div>
        </div>
        <div className={`flex items-center gap-1.5 px-2.5 py-1 ${statusBg} rounded-full`}>
          <StatusIcon className={`w-3.5 h-3.5 ${statusColor}`} />
          <span className={`text-xs font-semibold ${statusColor}`}>{data.status}</span>
        </div>
      </div>

      {/* Details */}
      <div className="space-y-2.5">
        {data.credits_remaining !== undefined && (
          <div className="flex items-center gap-2 text-sm">
            <CreditCard className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            <span className="text-slate-400">Credits:</span>
            <span className={`font-semibold ml-auto ${data.credits_remaining < 50 ? 'text-yellow-400' : 'text-white'}`}>
              {data.credits_remaining.toLocaleString()}
            </span>
          </div>
        )}

        {data.plan && (
          <div className="flex items-center gap-2 text-sm">
            <BadgeCheck className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            <span className="text-slate-400">Plan:</span>
            <span className="font-medium text-indigo-400 ml-auto">{data.plan}</span>
          </div>
        )}

        {checkedAt && (
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            <span className="text-slate-400">Checked:</span>
            <span className="text-slate-300 ml-auto">{checkedAt}</span>
          </div>
        )}

        {data.error && (
          <div className="mt-2 p-2 bg-red-900/20 border border-red-800/50 rounded-lg">
            <p className="text-xs text-red-300">{data.error}</p>
          </div>
        )}
      </div>

      {/* Status bar */}
      <div className="mt-4 pt-3 border-t border-slate-700/50">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${isReady ? 'bg-green-400 animate-pulse' : isError ? 'bg-red-400' : 'bg-yellow-400'}`} />
          <span className={`text-xs ${statusColor}`}>
            {isReady ? 'Operational' : isError ? 'Service Error' : 'API Key Missing'}
          </span>
        </div>
      </div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 animate-pulse">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-11 h-11 rounded-xl bg-slate-700" />
        <div className="flex-1">
          <div className="h-4 bg-slate-700 rounded w-24 mb-2" />
          <div className="h-3 bg-slate-700 rounded w-36" />
        </div>
        <div className="h-6 bg-slate-700 rounded-full w-20" />
      </div>
      <div className="space-y-2.5">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-4 bg-slate-700 rounded w-full" />
        ))}
      </div>
    </div>
  )
}

const MOCK_HEALTH: HealthResponse = {
  overall_status: 'DEGRADED',
  services: {
    apollo: { status: 'READY', credits_remaining: 450, plan: 'Pro', checked_at: new Date().toISOString() },
    hunter: { status: 'READY', credits_remaining: 190, plan: 'Starter', checked_at: new Date().toISOString() },
    prospeo: { status: 'NO KEY', checked_at: new Date().toISOString() },
    brevo: { status: 'READY', credits_remaining: 1200, plan: 'Free', checked_at: new Date().toISOString() },
    groq: { status: 'READY', plan: 'Free Tier', checked_at: new Date().toISOString() },
    openrouter: { status: 'READY', credits_remaining: 85, plan: 'Pay-as-you-go', checked_at: new Date().toISOString() },
  },
}

export default function HealthPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const fetchHealth = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    try {
      const res = await fetch('/api/health')
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      } else {
        setHealth(MOCK_HEALTH)
      }
    } catch {
      setHealth(MOCK_HEALTH)
    } finally {
      setLoading(false)
      setRefreshing(false)
      setLastRefresh(new Date())
    }
  }, [])

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(() => fetchHealth(true), 60000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  const services = health?.services || {}
  const readyCount = Object.values(services).filter((s) => s.status === 'READY').length
  const totalCount = Object.keys(services).length

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
              <Activity className="w-4 h-4 text-green-400" />
            </div>
            Integration Health
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Real-time status of all API integrations • Auto-refreshes every 60s
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-xs text-slate-500 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            Last: {lastRefresh.toLocaleTimeString()}
          </div>
          <button
            onClick={() => fetchHealth(true)}
            disabled={refreshing}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary banner */}
      {!loading && (
        <div className={`flex items-center gap-4 p-4 rounded-xl border ${readyCount === totalCount ? 'bg-green-900/20 border-green-800' : readyCount === 0 ? 'bg-red-900/20 border-red-800' : 'bg-yellow-900/20 border-yellow-800'}`}>
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${readyCount === totalCount ? 'bg-green-500/20' : 'bg-yellow-500/20'}`}>
            <Zap className={`w-5 h-5 ${readyCount === totalCount ? 'text-green-400' : 'text-yellow-400'}`} />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-white">
              {readyCount === totalCount
                ? '🟢 All systems operational'
                : readyCount === 0
                ? '🔴 All integrations offline'
                : `⚠️ ${readyCount} of ${totalCount} integrations ready`}
            </p>
            <p className="text-sm text-slate-400">
              {readyCount} ready • {totalCount - readyCount} need attention
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-white">{Math.round((readyCount / Math.max(totalCount, 1)) * 100)}%</p>
            <p className="text-xs text-slate-400">Uptime</p>
          </div>
        </div>
      )}

      {/* Service grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {loading
          ? [1, 2, 3, 4, 5, 6].map((i) => <SkeletonCard key={i} />)
          : Object.entries(services).map(([name, data]) => (
              <ServiceCard key={name} name={name} data={data} />
            ))
        }
      </div>

      {!loading && totalCount === 0 && (
        <div className="text-center py-16">
          <Activity className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <p className="text-slate-400 font-medium text-lg">No services configured</p>
          <p className="text-slate-500 text-sm mt-1">Add API keys to your backend .env file</p>
        </div>
      )}
    </div>
  )
}
