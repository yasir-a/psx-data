import json
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from psx_data.exceptions import PSXNetworkError, PSXParseError
from psx_data.symbols import (
    Symbol,
    fetch_symbols,
    get_sectors,
    get_symbols,
    get_tickers,
    parse_symbols,
)


class TestSymbols(unittest.TestCase):

    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "symbols.json"
        self.fixture_json = fixture_path.read_text(encoding="utf-8")

    def test_symbol_model(self):
        sym = Symbol(
            symbol="HUBC",
            name="The Hub Power Company Limited",
            sector="POWER GENERATION & DISTRIBUTION",
        )
        self.assertEqual(sym.symbol, "HUBC")
        self.assertEqual(sym.name, "The Hub Power Company Limited")
        self.assertEqual(sym.sector, "POWER GENERATION & DISTRIBUTION")

    def test_parse_symbols(self):
        symbols = parse_symbols(self.fixture_json)
        self.assertEqual(len(symbols), 5)
        self.assertEqual(symbols[0].symbol, "HUBC")
        self.assertEqual(symbols[0].sector, "POWER GENERATION & DISTRIBUTION")

    def test_parse_symbols_invalid_json(self):
        with self.assertRaises(PSXParseError):
            parse_symbols("not valid json {")

    @patch("psx_data.symbols.urlopen")
    def test_fetch_symbols_success(self, mock_urlopen):
        mock_resp = mock_urlopen.return_value.__enter__.return_value
        mock_resp.read.return_value = self.fixture_json.encode("utf-8")

        data = fetch_symbols()
        self.assertIn("HUBC", data)

    @patch("psx_data.symbols.urlopen")
    def test_fetch_symbols_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Network down")
        with self.assertRaises(PSXNetworkError):
            fetch_symbols()

    @patch("psx_data.symbols.fetch_symbols")
    def test_get_symbols_with_filter(self, mock_fetch):
        mock_fetch.return_value = self.fixture_json

        # Filter by sector
        banks = get_symbols(sector="COMMERCIAL BANKS")
        self.assertEqual(len(banks), 1)
        self.assertEqual(banks[0].symbol, "MEBL")

        # Filter by query search
        sys_matches = get_symbols(query="Systems")
        self.assertEqual(len(sys_matches), 1)
        self.assertEqual(sys_matches[0].symbol, "SYS")

    @patch("psx_data.symbols.fetch_symbols")
    def test_get_tickers(self, mock_fetch):
        mock_fetch.return_value = self.fixture_json
        tickers = get_tickers()
        self.assertEqual(tickers, ["HUBC", "OGDC", "SYS", "MEBL", "LUCK"])

    @patch("psx_data.symbols.fetch_symbols")
    def test_get_sectors(self, mock_fetch):
        mock_fetch.return_value = self.fixture_json
        sectors = get_sectors()
        self.assertIn("CEMENT", sectors)
        self.assertIn("COMMERCIAL BANKS", sectors)
        self.assertEqual(len(sectors), 5)


if __name__ == "__main__":
    unittest.main()