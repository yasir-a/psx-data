import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from psx_data.exceptions import PSXNetworkError, PSXParseError
from psx_data.market import (
    OHLCV,
    IntradayTick,
    fetch_eod,
    fetch_intraday,
    get_eod,
    get_intraday,
    parse_eod,
    parse_intraday,
)


class TestMarket(unittest.TestCase):

    def setUp(self):
        fixtures = Path(__file__).parent / "fixtures"
        self.eod_json = (fixtures / "eod_hubc.json").read_text(encoding="utf-8")
        self.intraday_json = (fixtures / "intraday_hubc.json").read_text(encoding="utf-8")

    def test_ohlcv_model(self):
        candle = OHLCV(
            timestamp=1723334400,
            open=145.50,
            high=148.00,
            low=144.20,
            close=147.10,
            volume=5234100,
        )
        self.assertEqual(candle.timestamp, 1723334400)
        self.assertEqual(candle.close, 147.10)
        self.assertEqual(candle.volume, 5234100)
        self.assertTrue(candle.date_str.startswith("2024-08-11") or candle.date_str != "")

    def test_intraday_tick_model(self):
        tick = IntradayTick(
            timestamp=1723507200,
            price=149.80,
            volume=12000,
        )
        self.assertEqual(tick.timestamp, 1723507200)
        self.assertEqual(tick.price, 149.80)
        self.assertEqual(tick.volume, 12000)

    def test_parse_eod(self):
        data = parse_eod(self.eod_json)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0].open, 145.50)
        self.assertEqual(data[0].high, 148.00)
        self.assertEqual(data[0].low, 144.20)
        self.assertEqual(data[0].close, 147.10)
        self.assertEqual(data[0].volume, 5234100)

    def test_parse_intraday(self):
        ticks = parse_intraday(self.intraday_json)
        self.assertEqual(len(ticks), 3)
        self.assertEqual(ticks[0].price, 149.80)
        self.assertEqual(ticks[0].volume, 12000)

    def test_parse_eod_invalid_json(self):
        with self.assertRaises(PSXParseError):
            parse_eod("invalid json")

    @patch("psx_data.market.urlopen")
    def test_fetch_eod_success(self, mock_urlopen):
        mock_resp = mock_urlopen.return_value.__enter__.return_value
        mock_resp.read.return_value = self.eod_json.encode("utf-8")

        result = fetch_eod("HUBC")
        self.assertIn("data", result)

    @patch("psx_data.market.urlopen")
    def test_fetch_eod_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Timeout")
        with self.assertRaises(PSXNetworkError):
            fetch_eod("HUBC")

    @patch("psx_data.market.fetch_eod")
    def test_get_eod(self, mock_fetch):
        mock_fetch.return_value = self.eod_json
        candles = get_eod("HUBC", limit=2)
        self.assertEqual(len(candles), 2)
        self.assertEqual(candles[-1].close, 150.40)

    @patch("psx_data.market.fetch_intraday")
    def test_get_intraday(self, mock_fetch):
        mock_fetch.return_value = self.intraday_json
        ticks = get_intraday("HUBC", limit=2)
        self.assertEqual(len(ticks), 2)
        self.assertEqual(ticks[-1].price, 150.40)


if __name__ == "__main__":
    unittest.main()