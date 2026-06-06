'use client'

import { useEffect, useState } from 'react'
import {
  Download,
  FileSpreadsheet,
  Users,
  CheckCircle2,
  Loader2,
  Table2,
  Info,
} from 'lucide-react'

const CSV_COLUMNS = [
  { name: 'name', type: 'string', description: 'Full name of the contact' },
  { name: 'email', type: 'string', description: 'Email address of the contact' },
  { name: 'company', type: 'string', description: 'Company or organization name' },
  { name: 'role', type: 'string', description: 'Job title or role at the company' },
  { name: 'domain', type: 'string', description: 'Company domain targeted in campaign' },
  { name: 'status', type: 'enum', description: 'Outreach status: SENT, PENDING, FAILED' },
  { name: 'sent_at', type: 'datetime', description: 'Timestamp when email was sent (ISO 8601)' },
  { name: 'campaign_id', type: 'string', description: 'ID of the parent campaign' },
  { name: 'subject', type: 'string', description: 'Email subject line used' },
  { name: 'personalization_score', type: 'number', description: 'AI personalization quality score (0–100)' },
]

const TYPE_COLORS: Record<string, string> = {
  string: 'badge-blue',
  enum: 'badge-yellow',
  datetime: 'badge-green',
  number: 'badge-red',
}

export default function ExportPage() {
  const [leadCount, setLeadCount] = useState<number | null>(null)
  const [loadingCount, setLoadingCount] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [downloaded, setDownloaded] = useState(false)

  useEffect(() => {
    const fetchCount = async () => {
      try {
        const res = await fetch('/api/leads')
        if (res.ok) {
          const data = await res.json()
          const leads = Array.isArray(data) ? data : data.leads || []
          setLeadCount(leads.length)
        } else {
          setLeadCount(8) // mock
        }
      } catch {
        setLeadCount(8) // mock
      } finally {
        setLoadingCount(false)
      }
    }
    fetchCount()
  }, [])

  const handleDownload = async () => {
    setDownloading(true)
    setDownloaded(false)
    try {
      const res = await fetch('/api/export/csv')
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `growth-engine-leads-${new Date().toISOString().slice(0, 10)}.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        setDownloaded(true)
        setTimeout(() => setDownloaded(false), 3000)
      } else {
        alert('Export failed — ensure the backend is running')
      }
    } catch {
      alert('Network error — ensure the backend is running at http://localhost:8000')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Page header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
            <Download className="w-4 h-4 text-emerald-400" />
          </div>
          Export Lead Data
        </h2>
        <p className="text-slate-400 text-sm mt-1">
          Download all your discovered leads and outreach history as a CSV file
        </p>
      </div>

      {/* Hero download card */}
      <div className="relative overflow-hidden card bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 border-indigo-800/50">
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/5 rounded-full -translate-y-32 translate-x-32" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-purple-600/5 rounded-full translate-y-24 -translate-x-24" />

        <div className="relative flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <FileSpreadsheet className="w-8 h-8 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Lead Export</h3>
              <p className="text-slate-400 text-sm mt-0.5">CSV format • UTF-8 encoded • All campaigns</p>
              <div className="flex items-center gap-2 mt-2">
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-900/30 border border-emerald-800 rounded-full">
                  <Users className="w-3 h-3 text-emerald-400" />
                  {loadingCount ? (
                    <div className="w-12 h-3 bg-slate-700 rounded animate-pulse" />
                  ) : (
                    <span className="text-xs text-emerald-400 font-medium">{leadCount} records</span>
                  )}
                </div>
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-blue-900/30 border border-blue-800 rounded-full">
                  <Table2 className="w-3 h-3 text-blue-400" />
                  <span className="text-xs text-blue-400 font-medium">{CSV_COLUMNS.length} columns</span>
                </div>
              </div>
            </div>
          </div>

          <button
            onClick={handleDownload}
            disabled={downloading}
            className={`relative flex items-center gap-3 px-8 py-4 rounded-xl font-semibold text-white transition-all duration-200 shadow-lg text-lg flex-shrink-0 ${
              downloaded
                ? 'bg-green-600 hover:bg-green-500 shadow-green-500/20'
                : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-500/20 hover:shadow-indigo-500/30 hover:scale-105 active:scale-100'
            } disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100`}
          >
            {downloading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Preparing CSV...
              </>
            ) : downloaded ? (
              <>
                <CheckCircle2 className="w-5 h-5" />
                Downloaded!
              </>
            ) : (
              <>
                <Download className="w-5 h-5" />
                Download CSV
              </>
            )}
          </button>
        </div>
      </div>

      {/* Info banner */}
      <div className="flex items-start gap-3 p-4 bg-blue-950/30 border border-blue-800/40 rounded-xl">
        <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-slate-300">
          <p className="font-medium text-blue-300 mb-1">What's included in the export?</p>
          <p className="text-slate-400">
            The CSV contains every lead discovered across all campaigns, including contact details, outreach status,
            email subjects, and AI personalization scores. Data is sorted by most recently contacted first.
          </p>
        </div>
      </div>

      {/* Column reference table */}
      <div className="card p-0 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700 flex items-center gap-2">
          <Table2 className="w-4 h-4 text-slate-400" />
          <h3 className="font-semibold text-white">Column Reference</h3>
          <span className="ml-auto text-xs text-slate-400">{CSV_COLUMNS.length} columns</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-800/50">
                {['Column Name', 'Type', 'Description'].map((h) => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CSV_COLUMNS.map((col, i) => (
                <tr key={col.name} className="table-row">
                  <td className="px-5 py-3">
                    <code className="text-sm font-mono text-indigo-300 bg-indigo-950/40 px-2 py-0.5 rounded border border-indigo-900/40">
                      {col.name}
                    </code>
                  </td>
                  <td className="px-5 py-3">
                    <span className={TYPE_COLORS[col.type] || 'badge-blue'}>
                      {col.type}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-sm text-slate-300">{col.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Download again section */}
      <div className="text-center py-6 border-t border-slate-800">
        <p className="text-slate-400 text-sm mb-4">Ready to export your data?</p>
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="btn-primary inline-flex items-center gap-2 px-6 py-3"
        >
          {downloading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Preparing...
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              Download CSV ({loadingCount ?? '...'} records)
            </>
          )}
        </button>
      </div>
    </div>
  )
}
