import { useEffect, useState } from 'react'
import {
  TrendingUp,
  TrendingDown,
  Building2,
  Bell,
  Database,
  Search,
  RefreshCw,
  FileText,
  Activity,
  Calendar,
  Layers,
  ChevronRight,
  ExternalLink
} from 'lucide-react'
import {
  fetchIndices,
  fetchSymbols,
  fetchSectors,
  fetchAnnouncements,
  fetchEOD,
  fetchIntraday,
  fetchCompanyProfile,
  fetchDBStats,
  syncSymbolsToDb,
  syncEODToDb,
  type IndexSummary,
  type SymbolItem,
  type OHLCV,
  type IntradayTick,
  type Announcement,
  type CompanyProfile as CompanyProfileType,
  type DBStats
} from './api'

export default function App() {
  const [indices, setIndices] = useState<IndexSummary[]>([])
  const [sectors, setSectors] = useState<string[]>([])
  const [symbols, setSymbols] = useState<SymbolItem[]>([])
  const [selectedSymbol, setSelectedSymbol] = useState<string>('HUBC')
  const [selectedSector, setSelectedSector] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  
  // Data states for selected symbol
  const [profile, setProfile] = useState<CompanyProfileType | null>(null)
  const [eodCandles, setEodCandles] = useState<OHLCV[]>([])
  const [intradayTicks, setIntradayTicks] = useState<IntradayTick[]>([])
  const [announcements, setAnnouncements] = useState<Announcement[]>([])
  const [dbStats, setDbStats] = useState<DBStats>({ symbols: 0, announcements: 0, eod_candles: 0, company_profiles: 0 })
  
  // UI states
  const [viewMode, setViewMode] = useState<'market' | 'announcements' | 'db'>('market')
  const [chartMode, setChartMode] = useState<'eod' | 'intraday'>('eod')
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [notification, setNotification] = useState('')

  // 1. Initial load
  useEffect(() => {
    loadInitialData()
  }, [])

  // 2. Load data whenever selected symbol changes
  useEffect(() => {
    if (selectedSymbol) {
      loadSymbolDetails(selectedSymbol)
    }
  }, [selectedSymbol])

  async function loadInitialData() {
    try {
      const [idxData, secData, symData, stats] = await Promise.all([
        fetchIndices(),
        fetchSectors(),
        fetchSymbols('', '', false),
        fetchDBStats()
      ])
      setIndices(idxData)
      setSectors(secData)
      setSymbols(symData)
      setDbStats(stats)
    } catch (err) {
      console.error('Error loading initial data:', err)
    }
  }

  async function loadSymbolDetails(symbol: string) {
    setLoading(true)
    try {
      const [prof, eod, ticks, anns] = await Promise.all([
        fetchCompanyProfile(symbol).catch(() => null),
        fetchEOD(symbol, 30).catch(() => []),
        fetchIntraday(symbol, 30).catch(() => []),
        fetchAnnouncements(symbol, 15).catch(() => [])
      ])
      setProfile(prof)
      setEodCandles(eod)
      setIntradayTicks(ticks)
      setAnnouncements(anns)
    } finally {
      setLoading(false)
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    try {
      const filtered = await fetchSymbols(selectedSector, searchQuery)
      setSymbols(filtered)
      if (filtered.length > 0) {
        setSelectedSymbol(filtered[0].symbol)
      }
    } catch (err) {
      console.error('Search failed:', err)
    }
  }

  async function handleSyncSymbols() {
    setSyncing(true)
    try {
      const msg = await syncSymbolsToDb()
      setNotification(msg)
      const stats = await fetchDBStats()
      setDbStats(stats)
    } finally {
      setSyncing(false)
      setTimeout(() => setNotification(''), 4000)
    }
  }

  async function handleSyncEOD() {
    if (!selectedSymbol) return
    setSyncing(true)
    try {
      const msg = await syncEODToDb(selectedSymbol, 100)
      setNotification(msg)
      const stats = await fetchDBStats()
      setDbStats(stats)
    } finally {
      setSyncing(false)
      setTimeout(() => setNotification(''), 4000)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="bg-emerald-500/10 border border-emerald-500/20 p-2 rounded-xl text-emerald-400">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              PSX Data Portal <span className="text-xs bg-emerald-500/20 text-emerald-300 font-mono px-2 py-0.5 rounded">v0.2.0</span>
            </h1>
            <p className="text-xs text-slate-400">Pakistan Stock Exchange Analytics & Local Storage</p>
          </div>
        </div>

        {/* View mode toggle tabs */}
        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('market')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition ${
              viewMode === 'market' ? 'bg-slate-800 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Activity className="w-4 h-4" /> Market
          </button>
          <button
            onClick={() => setViewMode('announcements')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition ${
              viewMode === 'announcements' ? 'bg-slate-800 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Bell className="w-4 h-4" /> Announcements
          </button>
          <button
            onClick={() => setViewMode('db')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition ${
              viewMode === 'db' ? 'bg-slate-800 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Database className="w-4 h-4" /> SQLite Cache ({dbStats.symbols})
          </button>
        </div>
      </header>

      {/* Notification Toast */}
      {notification && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm px-4 py-2 text-center">
          {notification}
        </div>
      )}

      {/* Benchmark Indices Marquee Ticker */}
      <section className="bg-slate-900/80 border-b border-slate-800/80 px-6 py-2.5 overflow-x-auto flex items-center gap-6 scrollbar-none">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-emerald-400" /> Indices
        </div>
        {indices.length === 0 ? (
          <div className="text-xs text-slate-500">Loading live indices...</div>
        ) : (
          indices.map((idx) => {
            const isUp = idx.change >= 0
            return (
              <div
                key={idx.index}
                className="flex items-center gap-2 text-sm bg-slate-950/60 border border-slate-800 px-3 py-1 rounded-md shrink-0"
              >
                <span className="font-bold text-slate-200">{idx.index}</span>
                <span className="font-mono text-white">{idx.current.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                <span className={`flex items-center font-mono text-xs ${isUp ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {isUp ? <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> : <TrendingDown className="w-3.5 h-3.5 mr-0.5" />}
                  {isUp ? '+' : ''}{idx.percent_change.toFixed(2)}%
                </span>
              </div>
            )
          })
        )}
      </section>

      {/* Main Content Layout */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Symbol Search & Company Directory (4 cols) */}
        <aside className="lg:col-span-4 flex flex-col gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Search className="w-4 h-4 text-emerald-400" /> Listed Companies
            </h2>

            {/* Search form */}
            <form onSubmit={handleSearch} className="space-y-2">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search ticker or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Sector Dropdown */}
              <select
                value={selectedSector}
                onChange={(e) => {
                  setSelectedSector(e.target.value)
                  fetchSymbols(e.target.value, searchQuery).then(setSymbols)
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-emerald-500"
              >
                <option value="">All Sectors ({sectors.length})</option>
                {sectors.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </form>

            {/* Symbols List */}
            <div className="mt-4 max-h-[500px] overflow-y-auto space-y-1 pr-1">
              {symbols.slice(0, 100).map((sym) => (
                <button
                  key={sym.symbol}
                  onClick={() => setSelectedSymbol(sym.symbol)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center justify-between transition ${
                    selectedSymbol === sym.symbol
                      ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-200'
                      : 'hover:bg-slate-800/60 text-slate-300'
                  }`}
                >
                  <div>
                    <div className="font-bold font-mono">{sym.symbol}</div>
                    <div className="text-xs text-slate-400 truncate max-w-[200px]">{sym.name}</div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-600" />
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Right Column: Active Symbol Details, Charts, Profile (8 cols) */}
        <main className="lg:col-span-8 flex flex-col gap-6">
          {viewMode === 'market' && (
            <>
              {/* Active Symbol Header Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-black tracking-tight text-white font-mono">{selectedSymbol}</h2>
                    {profile?.sector && (
                      <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full border border-slate-700">
                        {profile.sector}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-400 mt-1">{profile?.name || selectedSymbol}</p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSyncEOD}
                    disabled={syncing}
                    className="flex items-center gap-1.5 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-2 rounded-lg transition"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} /> Cache to SQLite
                  </button>
                </div>
              </div>

              {/* Price & Chart Area */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
                  <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-400" /> Market Price History
                  </h3>
                  <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
                    <button
                      onClick={() => setChartMode('eod')}
                      className={`px-3 py-1 text-xs font-medium rounded ${
                        chartMode === 'eod' ? 'bg-slate-800 text-white' : 'text-slate-400'
                      }`}
                    >
                      EOD Candles
                    </button>
                    <button
                      onClick={() => setChartMode('intraday')}
                      className={`px-3 py-1 text-xs font-medium rounded ${
                        chartMode === 'intraday' ? 'bg-slate-800 text-white' : 'text-slate-400'
                      }`}
                    >
                      Intraday Ticks
                    </button>
                  </div>
                </div>

                {/* Table representation */}
                {loading ? (
                  <div className="py-12 text-center text-slate-500 text-sm">Loading market series...</div>
                ) : chartMode === 'eod' ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm font-mono">
                      <thead>
                        <tr className="text-slate-500 border-b border-slate-800 text-xs uppercase">
                          <th className="py-2">Date</th>
                          <th className="py-2 text-right">Open</th>
                          <th className="py-2 text-right">High</th>
                          <th className="py-2 text-right">Low</th>
                          <th className="py-2 text-right">Close</th>
                          <th className="py-2 text-right">Volume</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {eodCandles.slice(0, 10).map((c, i) => (
                          <tr key={i} className="hover:bg-slate-800/30">
                            <td className="py-2 text-slate-300">{c.date}</td>
                            <td className="py-2 text-right text-slate-400">{c.open.toFixed(2)}</td>
                            <td className="py-2 text-right text-emerald-400">{c.high.toFixed(2)}</td>
                            <td className="py-2 text-right text-rose-400">{c.low.toFixed(2)}</td>
                            <td className="py-2 text-right font-bold text-white">{c.close.toFixed(2)}</td>
                            <td className="py-2 text-right text-slate-400">{c.volume.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm font-mono">
                      <thead>
                        <tr className="text-slate-500 border-b border-slate-800 text-xs uppercase">
                          <th className="py-2">Time</th>
                          <th className="py-2 text-right">Price</th>
                          <th className="py-2 text-right">Volume</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {intradayTicks.slice(0, 10).map((t, i) => (
                          <tr key={i} className="hover:bg-slate-800/30">
                            <td className="py-2 text-slate-300">{t.time}</td>
                            <td className="py-2 text-right font-bold text-emerald-400">{t.price.toFixed(2)}</td>
                            <td className="py-2 text-right text-slate-400">{t.volume.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Company Fundamentals Card */}
              {profile && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-emerald-400" /> Fundamentals & Governance
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                      <div className="text-xs text-slate-500">Market Cap</div>
                      <div className="font-bold text-white font-mono mt-1">
                        {profile.market_cap ? `PKR ${(profile.market_cap / 1e9).toFixed(2)}B` : '—'}
                      </div>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                      <div className="text-xs text-slate-500">Shares Listed</div>
                      <div className="font-bold text-white font-mono mt-1">
                        {profile.shares_listed ? (profile.shares_listed / 1e6).toFixed(2) + 'M' : '—'}
                      </div>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                      <div className="text-xs text-slate-500">Free Float</div>
                      <div className="font-bold text-white font-mono mt-1">
                        {profile.free_float ? (profile.free_float / 1e6).toFixed(2) + 'M' : '—'}
                      </div>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                      <div className="text-xs text-slate-500">Chief Executive (CEO)</div>
                      <div className="font-medium text-slate-200 mt-1 truncate">{profile.ceo || '—'}</div>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                      <div className="text-xs text-slate-500">Chairperson</div>
                      <div className="font-medium text-slate-200 mt-1 truncate">{profile.chairperson || '—'}</div>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                      <div className="text-xs text-slate-500">Auditor</div>
                      <div className="font-medium text-slate-200 mt-1 truncate">{profile.auditor || '—'}</div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Announcements Tab */}
          {viewMode === 'announcements' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <Bell className="w-5 h-5 text-emerald-400" /> Corporate Announcements ({selectedSymbol})
              </h2>
              {announcements.length === 0 ? (
                <div className="text-slate-500 py-8 text-center">No announcements found.</div>
              ) : (
                <div className="space-y-3">
                  {announcements.map((a, i) => (
                    <div key={i} className="bg-slate-950 border border-slate-800 p-4 rounded-xl flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2 text-xs text-slate-400 font-mono mb-1">
                          <Calendar className="w-3.5 h-3.5 text-slate-500" /> {a.date} • {a.time}
                        </div>
                        <h4 className="font-semibold text-slate-100">{a.title}</h4>
                        <p className="text-xs text-slate-500 mt-0.5">{a.name}</p>
                      </div>
                      {a.pdf_url && (
                        <a
                          href={a.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-lg hover:bg-emerald-500/20 transition shrink-0"
                        >
                          <FileText className="w-3.5 h-3.5" /> PDF <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* SQLite Cache Manager Tab */}
          {viewMode === 'db' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <Database className="w-5 h-5 text-emerald-400" /> Local SQLite Storage Layer
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                  <div className="text-2xl font-bold font-mono text-emerald-400">{dbStats.symbols.toLocaleString()}</div>
                  <div className="text-xs text-slate-400 mt-1">Symbols</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                  <div className="text-2xl font-bold font-mono text-emerald-400">{dbStats.announcements.toLocaleString()}</div>
                  <div className="text-xs text-slate-400 mt-1">Announcements</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                  <div className="text-2xl font-bold font-mono text-emerald-400">{dbStats.eod_candles.toLocaleString()}</div>
                  <div className="text-xs text-slate-400 mt-1">EOD Candles</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                  <div className="text-2xl font-bold font-mono text-emerald-400">{dbStats.company_profiles.toLocaleString()}</div>
                  <div className="text-xs text-slate-400 mt-1">Profiles</div>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleSyncSymbols}
                  disabled={syncing}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition flex items-center gap-2"
                >
                  <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} /> Sync All Symbols to SQLite
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}