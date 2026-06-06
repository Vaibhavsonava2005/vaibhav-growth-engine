'use client'

import { useEffect, useState, useMemo } from 'react'
import {
  Users,
  Search,
  Filter,
  Download,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
  Mail,
  Building2,
  User,
  RefreshCw,
} from 'lucide-react'

interface Lead {
  id?: string
  name?: string
  first_name?: string
  last_name?: string
  email: string
  company?: string
  organization_name?: string
  title?: string
  role?: string
  domain?: string
  status?: string
  sent_at?: string
  created_at?: string
}

const PAGE_SIZE = 25

function getStatusBadge(status?: string) {
  if (!status) return <span className="badge-blue">Unknown</span>
  switch (status.toUpperCase()) {
    case 'SENT':
      return <span className="badge-green"><CheckCircle2 className="w-3 h-3" />Sent</span>
    case 'FAILED':
      return <span className="badge-red"><XCircle className="w-3 h-3" />Failed</span>
    case 'PENDING':
      return <span className="badge-yellow"><Clock className="w-3 h-3" />Pending</span>
    default:
      return <span className="badge-blue">{status}</span>
  }
}

function SkeletonRow() {
  return (
    <tr className="border-b border-slate-700/50">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-slate-700 rounded animate-pulse" style={{ width: `${50 + i * 7}%` }} />
        </td>
      ))}
    </tr>
  )
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [search, setSearch] = useState('')
  const [domainFilter, setDomainFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [exporting, setExporting] = useState(false)

  const fetchLeads = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    try {
      const res = await fetch('/api/leads')
      if (res.ok) {
        const data = await res.json()
        setLeads(Array.isArray(data) ? data : data.leads || [])
      } else {
        // Mock data
        setLeads([
          { id: '1', name: 'Alice Johnson', email: 'alice@acme.com', company: 'Acme Corp', role: 'VP Marketing', domain: 'acme.com', status: 'SENT', sent_at: new Date(Date.now() - 3600000 * 2).toISOString() },
          { id: '2', name: 'Bob Smith', email: 'bob@techcorp.io', company: 'TechCorp', role: 'CTO', domain: 'techcorp.io', status: 'SENT', sent_at: new Date(Date.now() - 86400000).toISOString() },
          { id: '3', name: 'Carol White', email: 'carol@startup.co', company: 'Startup Co', role: 'CEO', domain: 'startup.co', status: 'PENDING', sent_at: undefined },
          { id: '4', name: 'David Lee', email: 'david@saas.app', company: 'SaaS App', role: 'Head of Sales', domain: 'saas.app', status: 'FAILED', sent_at: new Date(Date.now() - 3600000 * 5).toISOString() },
          { id: '5', name: 'Eva Martinez', email: 'eva@devtools.io', company: 'DevTools', role: 'Engineering Lead', domain: 'devtools.io', status: 'SENT', sent_at: new Date().toISOString() },
          { id: '6', name: 'Frank Brown', email: 'frank@acme.com', company: 'Acme Corp', role: 'Product Manager', domain: 'acme.com', status: 'SENT', sent_at: new Date(Date.now() - 3600000 * 8).toISOString() },
          { id: '7', name: 'Grace Kim', email: 'grace@techcorp.io', company: 'TechCorp', role: 'Marketing Director', domain: 'techcorp.io', status: 'PENDING', sent_at: undefined },
          { id: '8', name: 'Henry Davis', email: 'henry@crm.co', company: 'CRM Co', role: 'COO', domain: 'crm.co', status: 'SENT', sent_at: new Date(Date.now() - 86400000 * 2).toISOString() },
        ])
      }
    } catch {
      setLeads([])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchLeads()
  }, [])

  const domains = useMemo(() => {
    const all = leads.map((l) => l.domain).filter(Boolean) as string[]
    return ['all', ...Array.from(new Set(all))]
  }, [leads])

  const filtered = useMemo(() => {
    return leads.filter((l) => {
      const name = l.name || `${l.first_name || ''} ${l.last_name || ''}`.trim()
      const matchesSearch =
        !search ||
        name.toLowerCase().includes(search.toLowerCase()) ||
        l.email.toLowerCase().includes(search.toLowerCase()) ||
        (l.company || l.organization_name || '').toLowerCase().includes(search.toLowerCase())
      const matchesDomain = domainFilter === 'all' || l.domain === domainFilter
      return matchesSearch && matchesDomain
    })
  }, [leads, search, domainFilter])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleExport = async () => {
    setExporting(true)
    try {
      const res = await fetch('/api/export/csv')
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `leads-${new Date().toISOString().slice(0, 10)}.csv`
        a.click()
        window.URL.revokeObjectURL(url)
      } else {
        alert('Export failed — backend may not be running')
      }
    } catch {
      alert('Export failed — network error')
    } finally {
      setExporting(false)
    }
  }

  const handleSearchChange = (v: string) => {
    setSearch(v)
    setPage(1)
  }

  const handleDomainChange = (v: string) => {
    setDomainFilter(v)
    setPage(1)
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <Users className="w-4 h-4 text-purple-400" />
            </div>
            Leads
          </h2>
          <p className="text-slate-400 text-sm mt-1">All discovered contacts and outreach status</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchLeads(true)}
            disabled={refreshing}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="btn-primary flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            {exporting ? 'Exporting...' : 'Export CSV'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name, email, or company..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="input w-full pl-9"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <select
            value={domainFilter}
            onChange={(e) => handleDomainChange(e.target.value)}
            className="input pl-9 pr-8 appearance-none cursor-pointer min-w-[180px]"
          >
            {domains.map((d) => (
              <option key={d} value={d} className="bg-slate-800">
                {d === 'all' ? 'All Domains' : d}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results count */}
      <div className="flex items-center justify-between text-sm text-slate-400">
        <span>
          Showing <span className="text-white font-medium">{(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filtered.length)}</span> of <span className="text-white font-medium">{filtered.length}</span> leads
        </span>
        {filtered.length !== leads.length && (
          <span className="text-indigo-400">Filtered from {leads.length} total</span>
        )}
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-800/50">
                {['Name', 'Company', 'Email', 'Role', 'Status', 'Sent At'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading
                ? [1, 2, 3, 4, 5].map((i) => <SkeletonRow key={i} />)
                : paginated.length === 0
                ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-16 text-center">
                      <Users className="w-12 h-12 mx-auto text-slate-600 mb-3" />
                      <p className="text-slate-400 font-medium">
                        {search || domainFilter !== 'all' ? 'No leads match your filters' : 'No leads found'}
                      </p>
                      <p className="text-slate-500 text-sm mt-1">
                        {search || domainFilter !== 'all' ? 'Try adjusting your search or filter' : 'Run a campaign to discover leads'}
                      </p>
                    </td>
                  </tr>
                )
                : paginated.map((l, i) => {
                    const name = l.name || `${l.first_name || ''} ${l.last_name || ''}`.trim() || 'Unknown'
                    const company = l.company || l.organization_name || '—'
                    return (
                      <tr key={l.id || i} className="table-row">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center flex-shrink-0">
                              <User className="w-3.5 h-3.5 text-indigo-400" />
                            </div>
                            <span className="text-sm font-medium text-white">{name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5 text-sm text-slate-300">
                            <Building2 className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                            {company}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5 text-sm text-slate-300">
                            <Mail className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                            <a href={`mailto:${l.email}`} className="hover:text-indigo-400 transition-colors">
                              {l.email}
                            </a>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-300">{l.role || l.title || '—'}</td>
                        <td className="px-4 py-3">{getStatusBadge(l.status)}</td>
                        <td className="px-4 py-3 text-sm text-slate-400">
                          {l.sent_at ? (
                            <div className="flex items-center gap-1.5">
                              <Clock className="w-3 h-3" />
                              {new Date(l.sent_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </div>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                      </tr>
                    )
                  })
              }
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div className="px-6 py-4 border-t border-slate-700 flex items-center justify-between">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed text-sm px-3 py-1.5"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <div className="flex items-center gap-2">
              {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                const p = i + 1
                return (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                      p === page
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:text-white hover:bg-slate-700'
                    }`}
                  >
                    {p}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-secondary flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed text-sm px-3 py-1.5"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
