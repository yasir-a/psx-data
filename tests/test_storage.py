import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from psx_data.announcements import Announcement
from psx_data.exceptions import PSXNetworkError
from psx_data.storage import (
    download_attachment,
    export_to_csv,
    export_to_json,
)


class TestStorage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name)
        self.sample_announcements = [
            Announcement(
                date="Aug 11, 2026",
                time="3:22 PM",
                symbol="HUBC",
                name="The Hub Power Company Limited",
                title="Disclosure of Interest",
                image="281033-1.gif",
                pdf="/download/document/281033.pdf",
            )
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("psx_data.storage.urlopen")
    def test_download_attachment_success(self, mock_urlopen):
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = b"%PDF-1.4 mock content"

        file_path = download_attachment(
            url="https://dps.psx.com.pk/download/document/281033.pdf",
            destination_dir=self.path,
        )

        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.name, "281033.pdf")
        self.assertEqual(file_path.read_bytes(), b"%PDF-1.4 mock content")

    @patch("psx_data.storage.urlopen")
    def test_download_attachment_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Host unreachable")

        with self.assertRaises(PSXNetworkError):
            download_attachment(
                url="https://dps.psx.com.pk/download/document/281033.pdf",
                destination_dir=self.path,
            )

    def test_export_to_csv(self):
        csv_file = self.path / "announcements.csv"
        result_path = export_to_csv(self.sample_announcements, csv_file)

        self.assertEqual(result_path, csv_file)
        self.assertTrue(csv_file.exists())

        with csv_file.open("r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 1)
            self.assertEqual(reader[0]["symbol"], "HUBC")
            self.assertEqual(
                reader[0]["pdf_url"],
                "https://dps.psx.com.pk/download/document/281033.pdf",
            )

    def test_export_to_json(self):
        json_file = self.path / "announcements.json"
        result_path = export_to_json(self.sample_announcements, json_file)

        self.assertEqual(result_path, json_file)
        self.assertTrue(json_file.exists())

        data = json.loads(json_file.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["symbol"], "HUBC")
        self.assertEqual(
            data[0]["image_urls"],
            ["https://dps.psx.com.pk/download/image/281033-1.gif"],
        )


if __name__ == "__main__":
    unittest.main()