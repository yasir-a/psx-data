import sqlite3
import tempfile
import unittest
from pathlib import Path

from psx_data.announcements import Announcement
from psx_data.db import (
    get_connection,
    init_db,
    query_announcements,
    query_eod,
    query_symbols,
    save_announcements,
    save_eod,
    save_symbols,
)
from psx_data.market import OHLCV
from psx_data.symbols import Symbol


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_psx.db"
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_db_creates_tables(self):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}
            self.assertIn("symbols", tables)
            self.assertIn("announcements", tables)
            self.assertIn("eod_candles", tables)
        finally:
            conn.close()

    def test_save_and_query_symbols(self):
        symbols = [
            Symbol(symbol="HUBC", name="The Hub Power Company Limited", sector="POWER"),
            Symbol(symbol="SYS", name="Systems Limited", sector="TECHNOLOGY"),
        ]
        count = save_symbols(symbols, db_path=self.db_path)
        self.assertEqual(count, 2)

        results = query_symbols(db_path=self.db_path)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].symbol, "HUBC")

        # Query with sector filter
        tech_only = query_symbols(db_path=self.db_path, sector="TECHNOLOGY")
        self.assertEqual(len(tech_only), 1)
        self.assertEqual(tech_only[0].symbol, "SYS")

    def test_save_and_query_announcements(self):
        announcements = [
            Announcement(
                date="Aug 20, 2026",
                time="3:00 PM",
                symbol="HUBC",
                name="Hub Power",
                title="Board Meeting Notice",
                image="img1.gif",
                pdf="/doc1.pdf",
            )
        ]
        count = save_announcements(announcements, db_path=self.db_path)
        self.assertEqual(count, 1)

        saved = query_announcements(symbol="HUBC", db_path=self.db_path)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].title, "Board Meeting Notice")
        self.assertEqual(saved[0].pdf, "/doc1.pdf")

    def test_save_and_query_eod(self):
        candles = [
            OHLCV(timestamp=1723334400, open=145.0, high=148.0, low=144.0, close=147.0, volume=50000),
            OHLCV(timestamp=1723420800, open=147.0, high=150.0, low=146.0, close=149.0, volume=60000),
        ]
        count = save_eod(symbol="HUBC", candles=candles, db_path=self.db_path)
        self.assertEqual(count, 2)

        history = query_eod(symbol="HUBC", db_path=self.db_path, limit=10)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].open, 145.0)
        self.assertEqual(history[1].close, 149.0)
    
    def test_get_db_stats(self):
        from psx_data.db import get_db_stats

        stats = get_db_stats(db_path=self.db_path)
        self.assertEqual(stats["symbols"], 0)
        self.assertEqual(stats["announcements"], 0)
        self.assertEqual(stats["eod_candles"], 0)

        # Save symbol and verify count increases
        save_symbols([Symbol(symbol="HUBC", name="Hub Power", sector="POWER")], db_path=self.db_path)
        stats = get_db_stats(db_path=self.db_path)
        self.assertEqual(stats["symbols"], 1)


if __name__ == "__main__":
    unittest.main()