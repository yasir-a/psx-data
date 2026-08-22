import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
    

from psx_data.announcements import Announcement, fetch_announcements
from psx_data.exceptions import PSXNetworkError


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
    
    @patch("psx_data.announcements.urlopen")
    def test_fetch_announcements_raises_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Connection timed out")

        with self.assertRaises(PSXNetworkError):
            fetch_announcements(symbol="HUBC")
    
    def test_announcement_model(self):
        announcement = Announcement(
            date="Aug 11, 2026",
            time="3:22 PM",
            symbol="HUBC",
            name="The Hub Power Company Limited",
            title="Disclosure of Interest",
            image="281033-1.gif",
            pdf=None,
        )

        self.assertEqual(announcement.symbol, "HUBC")
        self.assertEqual(announcement.date, "Aug 11, 2026")
        self.assertEqual(announcement.time, "3:22 PM")
        self.assertEqual(
            announcement.name,
            "The Hub Power Company Limited",
        )
        self.assertEqual(announcement.image, "281033-1.gif")
        self.assertIsNone(announcement.pdf)
    
    def test_announcement_attachment_urls(self):
        announcement = Announcement(
            date="May 19, 2026",
            time="3:05 PM",
            symbol="HUBC",
            name="The Hub Power Company Limited",
            title="Dividend Notice",
            image="277488-1.gif, 277488-2.gif",
            pdf="/download/document/277488.pdf",
        )

        self.assertEqual(
            announcement.pdf_url,
            "https://dps.psx.com.pk/download/document/277488.pdf",
        )
        self.assertEqual(
            announcement.image_urls,
            [
                "https://dps.psx.com.pk/download/image/277488-1.gif",
                "https://dps.psx.com.pk/download/image/277488-2.gif",
            ],
        )

    def test_announcement_attachment_urls_when_empty(self):
        announcement = Announcement(
            date="Aug 11, 2026",
            time="3:22 PM",
            symbol="HUBC",
            name="The Hub Power Company Limited",
            title="Disclosure",
            image=None,
            pdf=None,
        )

        self.assertIsNone(announcement.pdf_url)
        self.assertEqual(announcement.image_urls, [])

    def test_parse_announcements(self):
        from psx_data.announcements import parse_announcements

        html = (
            Path(__file__).parent
            / "fixtures"
            / "announcements_hubc.html"
        ).read_text(encoding="utf-8")

        announcements = parse_announcements(html)

        self.assertEqual(len(announcements), 15)

        first = announcements[0]

        self.assertEqual(first.date, "Aug 11, 2026")
        self.assertEqual(first.time, "3:22 PM")
        self.assertEqual(first.symbol, "HUBC")
        self.assertEqual(first.name, "The Hub Power Company Limited")
        self.assertEqual(first.image, "281033-1.gif")
        self.assertIsNone(first.pdf)

    def test_parse_announcements_extracts_image_and_pdf(self):
        from psx_data.announcements import parse_announcements

        html = (
            Path(__file__).parent
            / "fixtures"
            / "announcements_hubc.html"
        ).read_text(encoding="utf-8")

        announcements = parse_announcements(html)

        second = announcements[1]

        self.assertEqual(second.symbol, "HUBC")
        self.assertEqual(second.image, "277488-1.gif")
        self.assertEqual(
            second.pdf,
            "/download/document/277488.pdf",
        )

    @patch("psx_data.announcements.parse_announcements")
    @patch("psx_data.announcements.fetch_announcements")
    def test_get_announcements_fetches_and_parses(
        self,
        mock_fetch,
        mock_parse,
    ):
        html = "<html>PSX announcements</html>"
        expected = [
            Announcement(
                date="Aug 11, 2026",
                time="3:22 PM",
                symbol="HUBC",
                name="The Hub Power Company Limited",
                title="Disclosure of Interest",
                image="281033-1.gif",
                pdf=None,
            )
        ]

        mock_fetch.return_value = html
        mock_parse.return_value = expected

        from psx_data.announcements import get_announcements

        result = get_announcements(
            symbol="HUBC",
            count=50,
            offset=0,
            date_from="2026-01-01",
            date_to="2026-08-10",
        )

        self.assertEqual(result, expected)

        mock_fetch.assert_called_once_with(
            symbol="HUBC",
            count=50,
            offset=0,
            date_from="2026-01-01",
            date_to="2026-08-10",
            timeout=10.0,
        )
        mock_parse.assert_called_once_with(html)
        
    @patch("psx_data.announcements.parse_announcements")
    @patch("psx_data.announcements.fetch_announcements")
    def test_get_announcements_supports_pagination(
        self,
        mock_fetch,
        mock_parse,
    ):
        html = "<html>PSX announcements</html>"
        expected = []

        mock_fetch.return_value = html
        mock_parse.return_value = expected

        from psx_data import get_announcements

        result = get_announcements(
            symbol="HUBC",
            count=15,
            offset=15,
        )

        self.assertEqual(result, expected)

        mock_fetch.assert_called_once_with(
            symbol="HUBC",
            count=15,
            offset=15,
            date_from="",
            date_to="",
            timeout=10.0,
        )
        mock_parse.assert_called_once_with(html)

    @patch("psx_data.announcements.parse_announcements")
    @patch("psx_data.announcements.fetch_announcements")
    def test_get_announcements_supports_date_filters(
        self,
        mock_fetch,
        mock_parse,
    ):
        html = "<html>PSX announcements</html>"
        expected = []

        mock_fetch.return_value = html
        mock_parse.return_value = expected

        from psx_data import get_announcements

        result = get_announcements(
            symbol="HUBC",
            date_from="2026-01-01",
            date_to="2026-08-10",
        )

        self.assertEqual(result, expected)

        mock_fetch.assert_called_once_with(
            symbol="HUBC",
            count=50,
            offset=0,
            date_from="2026-01-01",
            date_to="2026-08-10",
            timeout=10.0,
        )
        mock_parse.assert_called_once_with(html)

    @patch("psx_data.announcements.get_announcements")
    def test_iter_announcements_yields_all_pages(self, mock_get):
        first_page = [
            Announcement(
                date="Aug 11, 2026",
                time="3:22 PM",
                symbol="HUBC",
                name="The Hub Power Company Limited",
                title="First announcement",
                image="281033-1.gif",
                pdf=None,
            ),
            Announcement(
                date="May 19, 2026",
                time="3:05 PM",
                symbol="HUBC",
                name="The Hub Power Company Limited",
                title="Second announcement",
                image="277488-1.gif",
                pdf="/download/document/277488.pdf",
            ),
        ]

        second_page = [
            Announcement(
                date="Apr 29, 2026",
                time="2:10 PM",
                symbol="HUBC",
                name="The Hub Power Company Limited",
                title="Third announcement",
                image="275794-1.gif",
                pdf="/download/document/275794.pdf",
            )
        ]

        mock_get.side_effect = [first_page, second_page, []]

        from psx_data import iter_announcements

        result = list(
            iter_announcements(
                symbol="HUBC",
                count=2,
            )
        )

        self.assertEqual(
            result,
            first_page + second_page,
        )

        self.assertEqual(mock_get.call_count, 3)

        mock_get.assert_any_call(
            symbol="HUBC",
            count=2,
            offset=0,
            date_from="",
            date_to="",
            timeout=10.0,
        )

        mock_get.assert_any_call(
            symbol="HUBC",
            count=2,
            offset=2,
            date_from="",
            date_to="",
            timeout=10.0,
        )

        mock_get.assert_any_call(
            symbol="HUBC",
            count=2,
            offset=4,
            date_from="",
            date_to="",
            timeout=10.0,
        )  

if __name__ == "__main__":
    unittest.main()