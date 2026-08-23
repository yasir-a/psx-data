import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from psx_data.companies import (
    CompanyProfile,
    fetch_company_profile,
    get_company_profile,
    parse_company_profile,
)
from psx_data.exceptions import PSXNetworkError, PSXParseError


class TestCompanies(unittest.TestCase):

    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "company_hubc.html"
        self.fixture_html = fixture_path.read_text(encoding="utf-8")

    def test_company_profile_model(self):
        profile = CompanyProfile(
            symbol="HUBC",
            name="The Hub Power Company Limited",
            sector="POWER GENERATION & DISTRIBUTION",
            shares_listed=1297154387,
            free_float=972865790,
            market_cap=188735963308.0,
            ceo="Kamran Kamal",
            chairperson="M. Habibullah Khan",
            auditor="A. F. Ferguson & Co.",
            website="www.hubpower.com",
            address="9th Floor, Ocean Tower, Block 9, Clifton, Karachi",
            fiscal_year_end="June",
        )
        self.assertEqual(profile.symbol, "HUBC")
        self.assertEqual(profile.shares_listed, 1297154387)
        self.assertEqual(profile.ceo, "Kamran Kamal")

    def test_parse_company_profile_html(self):
        profile = parse_company_profile("HUBC", self.fixture_html)
        self.assertEqual(profile.symbol, "HUBC")
        self.assertIn("Hub Power", profile.name)
        self.assertEqual(profile.ceo, "Kamran Kamal")
        self.assertEqual(profile.chairperson, "M. Habibullah Khan")
        self.assertEqual(profile.auditor, "A. F. Ferguson & Co.")
        self.assertEqual(profile.website, "www.hubpower.com")
        self.assertIn("Karachi", profile.address)
        self.assertEqual(profile.shares_listed, 1297154387)
        self.assertEqual(profile.free_float, 972865790)
        self.assertEqual(profile.market_cap, 188735963308.0)

    def test_parse_company_profile_empty_returns_fallback(self):
        profile = parse_company_profile("HUBC", "<html><body></body></html>")
        self.assertEqual(profile.symbol, "HUBC")
        self.assertEqual(profile.shares_listed, 0)

    @patch("psx_data.companies.urlopen")
    def test_fetch_company_profile_success(self, mock_urlopen):
        mock_resp = mock_urlopen.return_value.__enter__.return_value
        mock_resp.read.return_value = self.fixture_html.encode("utf-8")

        html = fetch_company_profile("HUBC")
        self.assertIn("Hub Power", html)

    @patch("psx_data.companies.urlopen")
    def test_fetch_company_profile_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Network error")
        with self.assertRaises(PSXNetworkError):
            fetch_company_profile("HUBC")

    @patch("psx_data.companies.fetch_company_profile")
    def test_get_company_profile(self, mock_fetch):
        mock_fetch.return_value = self.fixture_html
        profile = get_company_profile("HUBC")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.symbol, "HUBC")
        self.assertEqual(profile.ceo, "Kamran Kamal")


if __name__ == "__main__":
    unittest.main()