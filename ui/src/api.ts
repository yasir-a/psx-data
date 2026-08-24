export interface IndexSummary {
  index: string
  name: string
  current: number
  change: number
  percent_change: number
  high: number
  low: number
  volume: number
  status: string
}

export interface SymbolItem {
  symbol: string
  name: string
  sector: string
}

export interface OHLCV {
  timestamp: number
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface IntradayTick {
  timestamp: number
  time: string
  price: number
  volume: number
}

export interface Announcement {
  date: string
  time: string
  symbol: string
  name: string
  title: string
  image?: string
  pdf?: string
  pdf_url?: string
  image_urls?: string[]
}

export interface CompanyProfile {
  symbol: string
  name: string
  sector: string
  shares_listed: number
  free_float: number
  market_cap: number
  ceo: string
  chairperson: string
  auditor: string
  website: string
  address: string
  fiscal_year_end: string
}

export interface DBStats {
  symbols: number
  announcements: number
  eod_candles: number
  company_profiles: number
}

const BASE_URL = '/api'

export async function fetchIndices(): Promise<IndexSummary[]> {
  const res = await fetch(`${BASE_URL}/indices`)
  const json = await res.json()
  return json.data || []
}

export async function fetchSymbols(sector = '', query = '', fromDb = false): Promise<SymbolItem[]> {
  const params = new URLSearchParams()
  if (sector) params.append('sector', sector)
  if (query) params.append('query', query)
  if (fromDb) params.append('from_db', 'true')
  const res = await fetch(`${BASE_URL}/symbols?${params.toString()}`)
  const json = await res.json()
  return json.data || []
}

export async function fetchSectors(): Promise<string[]> {
  const res = await fetch(`${BASE_URL}/sectors`)
  const json = await res.json()
  return json.data || []
}

export async function fetchAnnouncements(symbol = '', count = 20, fromDb = false): Promise<Announcement[]> {
  const params = new URLSearchParams()
  if (symbol) params.append('symbol', symbol)
  params.append('count', String(count))
  if (fromDb) params.append('from_db', 'true')
  const res = await fetch(`${BASE_URL}/announcements?${params.toString()}`)
  const json = await res.json()
  return json.data || []
}

export async function fetchEOD(symbol: string, limit = 50, fromDb = false): Promise<OHLCV[]> {
  const params = new URLSearchParams()
  params.append('symbol', symbol)
  params.append('limit', String(limit))
  if (fromDb) params.append('from_db', 'true')
  const res = await fetch(`${BASE_URL}/eod?${params.toString()}`)
  const json = await res.json()
  return json.data || []
}

export async function fetchIntraday(symbol: string, limit = 50): Promise<IntradayTick[]> {
  const res = await fetch(`${BASE_URL}/intraday?symbol=${encodeURIComponent(symbol)}&limit=${limit}`)
  const json = await res.json()
  return json.data || []
}

export async function fetchCompanyProfile(symbol: string, fromDb = false): Promise<CompanyProfile | null> {
  const params = new URLSearchParams()
  params.append('symbol', symbol)
  if (fromDb) params.append('from_db', 'true')
  const res = await fetch(`${BASE_URL}/company?${params.toString()}`)
  if (!res.ok) return null
  const json = await res.json()
  return json.data || null
}

export async function fetchDBStats(): Promise<DBStats> {
  const res = await fetch(`${BASE_URL}/status`)
  const json = await res.json()
  return json.db_stats || { symbols: 0, announcements: 0, eod_candles: 0, company_profiles: 0 }
}

export async function syncSymbolsToDb(): Promise<string> {
  const res = await fetch(`${BASE_URL}/sync/symbols`, { method: 'POST' })
  const json = await res.json()
  return json.message || 'Synced'
}

export async function syncEODToDb(symbol: string, limit = 100): Promise<string> {
  const res = await fetch(`${BASE_URL}/sync/eod`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, limit }),
  })
  const json = await res.json()
  return json.message || 'Synced'
}