import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from psx_data.exceptions import PSXNetworkError, PSXParseError
from psx_data.financials import (
    DividendRecord,
    FinancialRatio,
    FinancialSummary,
    fetch_financials,
    get_financials,
    parse_dividends,
    parse_financials,
    parse_ratios,
)


class TestFinancials(unittest.TestCase):

    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "financials_hubc.html"
        self.fixture_html = fixture_path.read_text(encoding="utf-8")

    def test_models_instantiation(self):
        div = DividendRecord(
            symbol="HUBC",
            announcement_date="2024-08-15",
            financial_year_end="June 2024",
            dividend_percent=140.0,
            dividend_amount=14.0,
            bonus_percent=0.0,
            right_percent=0.0,
        )
        self.assertEqual(div.symbol, "HUBC")
        self.assertEqual(div.dividend_amount, 14.0)

        ratio = FinancialRatio(
            symbol="HUBC",
            period="FY 2024",
            eps=45.80,
            pe_ratio=3.20,
            book_value=78.50,
            roe=38.5,
            dividend_yield=18.2,
        )
        self.assertEqual(ratio.eps, 45.80)
        self.assertEqual(ratio.pe_ratio, 3.20)

    def test_parse_ratios(self):
        ratios = parse_ratios("HUBC", self.fixture_html)
        self.assertEqual(len(ratios), 2)
        self.assertEqual(ratios[0].period, "FY 2024")
        self.assertEqual(ratios[0].eps, 45.80)
        self.assertEqual(ratios[0].pe_ratio, 3.20)
        self.assertEqual(ratios[1].period, "FY 2023")
        self.assertEqual(ratios[1].eps, 38.20)

    def test_parse_dividends(self):
        dividends = parse_dividends("HUBC", self.fixture_html)
        self.assertEqual(len(dividends), 3)
        self.assertEqual(dividends[0].announcement_date, "2024-08-15")
        self.assertEqual(dividends[0].dividend_amount, 14.0)
        self.assertEqual(dividends[2].bonus_percent, 10.0)

    def test_parse_financials_combined(self):
        summary = parse_financials("HUBC", self.fixture_html)
        self.assertEqual(summary.symbol, "HUBC")
        self.assertEqual(len(summary.ratios), 2)
        self.assertEqual(len(summary.dividends), 3)

    @patch("psx_data.financials.urlopen")
    def test_fetch_financials_success(self, mock_urlopen):
        mock_resp = mock_urlopen.return_value.__enter__.return_value
        mock_resp.read.return_value = self.fixture_html.encode("utf-8")

        html = fetch_financials("HUBC")
        self.assertIn("Financial Ratios", html)

    @patch("psx_data.financials.urlopen")
    def test_fetch_financials_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Timeout connecting to server")
        with self.assertRaises(PSXNetworkError):
            fetch_financials("HUBC")

    @patch("psx_data.financials.fetch_financials")
    def test_get_financials(self, mock_fetch):
        mock_fetch.return_value = self.fixture_html
        summary = get_financials("HUBC")
        self.assertEqual(summary.symbol, "HUBC")
        self.assertGreater(len(summary.ratios), 0)


if __name__ == "__main__":
    unittest.main()