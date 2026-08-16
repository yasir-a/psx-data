import unittest
from unittest.mock import patch

from psx_data.announcements import fetch_announcements


class TestFetchAnnouncements(unittest.TestCase):

    @patch("psx_data.announcements.urlopen")
    def test_fetch_announcements_returns_response(self, mock_urlopen):
        response = mock_urlopen.return_value.__enter__.return_value
        response.read.return_value = b"<html>PSX announcements</html>"

        result = fetch_announcements(symbol="HUBC")

        self.assertEqual(result, "<html>PSX announcements</html>")
        mock_urlopen.assert_called_once()

    @patch("psx_data.announcements.urlopen")
    def test_fetch_announcements_builds_request(self, mock_urlopen):
        response = mock_urlopen.return_value.__enter__.return_value
        response.read.return_value = b"<html></html>"

        fetch_announcements(
            symbol="HUBC",
            count=50,
            offset=0,
            date_from="2026-01-01",
            date_to="2026-08-10",
        )

        request = mock_urlopen.call_args.args[0]

        self.assertEqual(
            request.full_url,
            "https://dps.psx.com.pk/announcements",
        )
        self.assertEqual(request.method, "POST")
        self.assertEqual(
            request.data.decode("utf-8"),
            "type=C&symbol=HUBC&query=&count=50&offset=0"
            "&date_from=2026-01-01&date_to=2026-08-10&page=annc",
        )
        
    @patch("psx_data.announcements.urlopen")
    def test_fetch_announcements_encodes_parameters(self, mock_urlopen):
        response = mock_urlopen.return_value.__enter__.return_value
        response.read.return_value = b"<html></html>"

        fetch_announcements(symbol="ABC&XYZ")

        request = mock_urlopen.call_args.args[0]

        self.assertIn("symbol=ABC%26XYZ", request.data.decode("utf-8"))

if __name__ == "__main__":
    unittest.main()