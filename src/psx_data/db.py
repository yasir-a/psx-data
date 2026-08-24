"""SQLite local persistence and caching layer for psx-data."""

import sqlite3
from pathlib import Path

from psx_data.financials import DividendRecord, FinancialRatio, FinancialSummary
from psx_data.announcements import Announcement
from psx_data.companies import CompanyProfile
from psx_data.market import OHLCV
from psx_data.symbols import Symbol


DEFAULT_DB_PATH = Path("psx_data.db")



def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create and return a configured SQLite connection."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    """Initialize SQLite database tables and indexes."""
    path = Path(db_path)
    conn = get_connection(path)
    try:
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS symbols (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                image TEXT,
                pdf TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date, time, title)
            );

            CREATE TABLE IF NOT EXISTS eod_candles (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (symbol, timestamp)
            );

            CREATE TABLE IF NOT EXISTS company_profiles (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT NOT NULL DEFAULT '',
                shares_listed INTEGER DEFAULT 0,
                free_float INTEGER DEFAULT 0,
                market_cap REAL DEFAULT 0.0,
                ceo TEXT DEFAULT '',
                chairperson TEXT DEFAULT '',
                auditor TEXT DEFAULT '',
                website TEXT DEFAULT '',
                address TEXT DEFAULT '',
                fiscal_year_end TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS financial_ratios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                period TEXT NOT NULL,
                eps REAL DEFAULT 0.0,
                pe_ratio REAL DEFAULT 0.0,
                book_value REAL DEFAULT 0.0,
                price_to_book REAL DEFAULT 0.0,
                dividend_yield REAL DEFAULT 0.0,
                roe REAL DEFAULT 0.0,
                roa REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, period)
            );

            CREATE TABLE IF NOT EXISTS dividends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                announcement_date TEXT NOT NULL,
                financial_year_end TEXT NOT NULL DEFAULT '',
                dividend_percent REAL DEFAULT 0.0,
                dividend_amount REAL DEFAULT 0.0,
                bonus_percent REAL DEFAULT 0.0,
                right_percent REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, announcement_date, financial_year_end, dividend_amount)
            );

            CREATE INDEX IF NOT EXISTS idx_announcements_symbol ON announcements(symbol);
            CREATE INDEX IF NOT EXISTS idx_eod_symbol_timestamp ON eod_candles(symbol, timestamp);
            """
        )
        conn.commit()
    finally:
        conn.close()
    return path


def save_symbols(symbols: list[Symbol], db_path: str | Path = DEFAULT_DB_PATH) -> int:
    """Save or update listed symbols in the database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO symbols (symbol, name, sector, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(symbol) DO UPDATE SET
                name=excluded.name,
                sector=excluded.sector,
                updated_at=CURRENT_TIMESTAMP;
            """,
            [(s.symbol, s.name, s.sector) for s in symbols],
        )
        conn.commit()
        return len(symbols)
    finally:
        conn.close()


def query_symbols(
    db_path: str | Path = DEFAULT_DB_PATH,
    sector: str = "",
    query: str = "",
) -> list[Symbol]:
    """Query cached symbols from the database with optional filtering."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        sql = "SELECT symbol, name, sector FROM symbols WHERE 1=1"
        params: list[str] = []

        if sector:
            sql += " AND UPPER(sector) = ?"
            params.append(sector.strip().upper())

        if query:
            sql += " AND (UPPER(symbol) LIKE ? OR UPPER(name) LIKE ?)"
            term = f"%{query.strip().upper()}%"
            params.extend([term, term])

        sql += " ORDER BY symbol ASC"
        cursor.execute(sql, params)
        return [
            Symbol(symbol=row["symbol"], name=row["name"], sector=row["sector"])
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()


def save_announcements(
    announcements: list[Announcement],
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Save corporate announcements in the database (ignores duplicates)."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT OR IGNORE INTO announcements (symbol, date, time, name, title, image, pdf)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (a.symbol, a.date, a.time, a.name, a.title, a.image, a.pdf)
                for a in announcements
            ],
        )
        conn.commit()
        return len(announcements)
    finally:
        conn.close()


def query_announcements(
    symbol: str = "",
    limit: int = 50,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[Announcement]:
    """Query cached announcements from the database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        sql = "SELECT date, time, symbol, name, title, image, pdf FROM announcements"
        params: list[str | int] = []

        if symbol:
            sql += " WHERE UPPER(symbol) = ?"
            params.append(symbol.strip().upper())

        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        return [
            Announcement(
                date=row["date"],
                time=row["time"],
                symbol=row["symbol"],
                name=row["name"],
                title=row["title"],
                image=row["image"],
                pdf=row["pdf"],
            )
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()


def save_eod(
    symbol: str,
    candles: list[OHLCV],
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Save or update historical EOD OHLCV candles in the database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO eod_candles (symbol, date, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, timestamp) DO UPDATE SET
                open=excluded.open,
                high=excluded.high,
                low=excluded.low,
                close=excluded.close,
                volume=excluded.volume;
            """,
            [
                (
                    symbol.upper(),
                    c.date_str,
                    c.timestamp,
                    c.open,
                    c.high,
                    c.low,
                    c.close,
                    c.volume,
                )
                for c in candles
            ],
        )
        conn.commit()
        return len(candles)
    finally:
        conn.close()


def query_eod(
    symbol: str,
    limit: int = 50,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[OHLCV]:
    """Query historical EOD candles for a symbol from the database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT timestamp, open, high, low, close, volume
            FROM eod_candles
            WHERE UPPER(symbol) = ?
            ORDER BY timestamp ASC
            LIMIT ?;
            """,
            (symbol.strip().upper(), limit),
        )
        return [
            OHLCV(
                timestamp=row["timestamp"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
            )
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()

def get_db_stats(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, int]:
    """Get record counts for all tables in the SQLite database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        stats: dict[str, int] = {}
        for table in ["symbols", "announcements", "eod_candles", "company_profiles", "financial_ratios", "dividends"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        return stats
    finally:
        conn.close()

def save_company_profile(
    profile: CompanyProfile,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Save or update a company profile in the database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO company_profiles (
                symbol, name, sector, shares_listed, free_float, market_cap,
                ceo, chairperson, auditor, website, address, fiscal_year_end, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(symbol) DO UPDATE SET
                name=excluded.name,
                sector=excluded.sector,
                shares_listed=excluded.shares_listed,
                free_float=excluded.free_float,
                market_cap=excluded.market_cap,
                ceo=excluded.ceo,
                chairperson=excluded.chairperson,
                auditor=excluded.auditor,
                website=excluded.website,
                address=excluded.address,
                fiscal_year_end=excluded.fiscal_year_end,
                updated_at=CURRENT_TIMESTAMP;
            """,
            (
                profile.symbol.upper(),
                profile.name,
                profile.sector,
                profile.shares_listed,
                profile.free_float,
                profile.market_cap,
                profile.ceo,
                profile.chairperson,
                profile.auditor,
                profile.website,
                profile.address,
                profile.fiscal_year_end,
            ),
        )
        conn.commit()
        return 1
    finally:
        conn.close()


def query_company_profile(
    symbol: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> CompanyProfile | None:
    """Query cached company profile from SQLite database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT symbol, name, sector, shares_listed, free_float, market_cap,
                   ceo, chairperson, auditor, website, address, fiscal_year_end
            FROM company_profiles
            WHERE UPPER(symbol) = ?;
            """,
            (symbol.strip().upper(),),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return CompanyProfile(
            symbol=row["symbol"],
            name=row["name"],
            sector=row["sector"],
            shares_listed=row["shares_listed"],
            free_float=row["free_float"],
            market_cap=row["market_cap"],
            ceo=row["ceo"],
            chairperson=row["chairperson"],
            auditor=row["auditor"],
            website=row["website"],
            address=row["address"],
            fiscal_year_end=row["fiscal_year_end"],
        )
    finally:
        conn.close()

def save_financials(
    financials: FinancialSummary,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Save financial ratios and dividend records to SQLite database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        total_saved = 0

        for r in financials.ratios:
            cursor.execute(
                """
                INSERT INTO financial_ratios (
                    symbol, period, eps, pe_ratio, book_value, price_to_book, dividend_yield, roe, roa
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, period) DO UPDATE SET
                    eps=excluded.eps,
                    pe_ratio=excluded.pe_ratio,
                    book_value=excluded.book_value,
                    dividend_yield=excluded.dividend_yield,
                    roe=excluded.roe;
                """,
                (
                    r.symbol.upper(),
                    r.period,
                    r.eps,
                    r.pe_ratio,
                    r.book_value,
                    r.price_to_book,
                    r.dividend_yield,
                    r.roe,
                    r.roa,
                ),
            )
            total_saved += 1

        for d in financials.dividends:
            cursor.execute(
                """
                INSERT OR IGNORE INTO dividends (
                    symbol, announcement_date, financial_year_end, dividend_percent,
                    dividend_amount, bonus_percent, right_percent
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    d.symbol.upper(),
                    d.announcement_date,
                    d.financial_year_end,
                    d.dividend_percent,
                    d.dividend_amount,
                    d.bonus_percent,
                    d.right_percent,
                ),
            )
            total_saved += 1

        conn.commit()
        return total_saved
    finally:
        conn.close()


def query_financials(
    symbol: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> FinancialSummary:
    """Query cached financial ratios and dividends for a symbol from database."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        sym = symbol.strip().upper()

        cursor.execute(
            """
            SELECT symbol, period, eps, pe_ratio, book_value, price_to_book, dividend_yield, roe, roa
            FROM financial_ratios
            WHERE UPPER(symbol) = ?
            ORDER BY id ASC;
            """,
            (sym,),
        )
        ratios = [
            FinancialRatio(
                symbol=row["symbol"],
                period=row["period"],
                eps=row["eps"],
                pe_ratio=row["pe_ratio"],
                book_value=row["book_value"],
                price_to_book=row["price_to_book"],
                dividend_yield=row["dividend_yield"],
                roe=row["roe"],
                roa=row["roa"],
            )
            for row in cursor.fetchall()
        ]

        cursor.execute(
            """
            SELECT symbol, announcement_date, financial_year_end, dividend_percent,
                   dividend_amount, bonus_percent, right_percent
            FROM dividends
            WHERE UPPER(symbol) = ?
            ORDER BY announcement_date DESC;
            """,
            (sym,),
        )
        dividends = [
            DividendRecord(
                symbol=row["symbol"],
                announcement_date=row["announcement_date"],
                financial_year_end=row["financial_year_end"],
                dividend_percent=row["dividend_percent"],
                dividend_amount=row["dividend_amount"],
                bonus_percent=row["bonus_percent"],
                right_percent=row["right_percent"],
            )
            for row in cursor.fetchall()
        ]

        return FinancialSummary(symbol=sym, ratios=ratios, dividends=dividends)
    finally:
        conn.close()