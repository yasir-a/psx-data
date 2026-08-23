"""SQLite local persistence and caching layer for psx-data."""

import sqlite3
from pathlib import Path

from psx_data.announcements import Announcement
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