import io
import json
import unittest
from unittest.mock import patch

from psx_data.announcements import Announcement
from psx_data.cli import main
from psx_data.exceptions import PSXNetworkError


class TestCLI(unittest.TestCase):

    @patch("psx_data.cli.get_announcements")
    def test_cli_announcements_text_output(self, mock_get):
        mock_get.return_value = [
            Announcement(
                date="Aug 11, 2026",
                time="3:22 PM",
                symbol="HUBC",
                name="The Hub Power Company Limited",
                title="Disclosure of Interest",
                image=None,
                pdf="/download/document/281033.pdf",
            )
        ]

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = main(["announcements", "--symbol", "HUBC", "--count", "5"])

        self.assertEqual(exit_code, 0)
        output = fake_out.getvalue()
        self.assertIn("HUBC", output)
        self.assertIn("Disclosure of Interest", output)
        self.assertIn("https://dps.psx.com.pk/download/document/281033.pdf", output)

    @patch("psx_data.cli.get_announcements")
    def test_cli_announcements_json_output(self, mock_get):
        mock_get.return_value = [
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

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = main(["announcements", "--symbol", "HUBC", "--json"])

        self.assertEqual(exit_code, 0)
        data = json.loads(fake_out.getvalue())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["symbol"], "HUBC")
        self.assertEqual(data[0]["image_urls"], ["https://dps.psx.com.pk/download/image/281033-1.gif"])

    @patch("psx_data.cli.get_announcements")
    def test_cli_handles_network_error(self, mock_get):
        mock_get.side_effect = PSXNetworkError("Connection timed out")

        with patch("sys.stderr", new=io.StringIO()) as fake_err:
            exit_code = main(["announcements", "--symbol", "HUBC"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Connection timed out", fake_err.getvalue())

    @patch("psx_data.cli.export_to_csv")
    @patch("psx_data.cli.get_announcements")
    def test_cli_announcements_csv_export(self, mock_get, mock_export):
        mock_get.return_value = [
            Announcement(
                date="Aug 11, 2026",
                time="3:22 PM",
                symbol="HUBC",
                name="The Hub Power Company Limited",
                title="Disclosure of Interest",
                image=None,
                pdf=None,
            )
        ]
        mock_export.return_value = "hubc.csv"

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = main(["announcements", "--symbol", "HUBC", "--csv", "hubc.csv"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Saved 1 announcements to hubc.csv", fake_out.getvalue())
        mock_export.assert_called_once()

    @patch("psx_data.cli.download_attachment")
    @patch("psx_data.cli.get_announcements")
    def test_cli_announcements_download_dir(self, mock_get, mock_download):
        mock_get.return_value = [
            Announcement(
                date="Aug 11, 2026",
                time="3:22 PM",
                symbol="HUBC",
                name="The Hub Power Company Limited",
                title="Notice",
                image="281033-1.gif",
                pdf="/download/document/281033.pdf",
            )
        ]

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = main(["announcements", "--symbol", "HUBC", "--download-dir", "./downloads"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Downloaded 2 attachments", fake_out.getvalue())
        self.assertEqual(mock_download.call_count, 2)

if __name__ == "__main__":
    unittest.main()