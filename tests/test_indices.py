import json
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from psx_data.exceptions import PSXNetworkError, PSXParseError
from psx_data.indices import (
    IndexSummary,
    fetch_indices,
    get_index,
    get_indices,
    parse_indices,
)


class TestIndices(unittest.TestCase):

    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "indices.json"
        self.fixture_json = fixture_path.read_text(encoding="utf-8")

    def test_index_summary_model(self):
        idx = IndexSummary(
            index="KSE100",
            name="KSE 100 Index",
            current=78456.20,
            change=345.80,
            percent_change=0.44,
            high=78600.50,
            low=78100.10,
            volume=215430800,
            status="UP",
        )
        self.assertEqual(idx.index, "KSE100")
        self.assertEqual(idx.current, 78456.20)
        self.assertEqual(idx.change, 345.80)
        self.assertEqual(idx.percent_change, 0.44)
        self.assertEqual(idx.volume, 215430800)

    def test_parse_indices(self):
        indices = parse_indices(self.fixture_json)
        self.assertEqual(len(indices), 4)
        self.assertEqual(indices[0].index, "KSE100")
        self.assertEqual(indices[0].current, 78456.20)
        self.assertEqual(indices[1].index, "KSE30")
        self.assertEqual(indices[1].change, -85.20)

    def test_parse_indices_invalid_json(self):
        with self.assertRaises(PSXParseError):
            parse_indices("invalid json {")

    @patch("psx_data.indices.urlopen")
    def test_fetch_indices_success(self, mock_urlopen):
        mock_resp = mock_urlopen.return_value.__enter__.return_value
        mock_resp.read.return_value = self.fixture_json.encode("utf-8")

        result = fetch_indices()
        self.assertIn("KSE100", result)

    @patch("psx_data.indices.urlopen")
    def test_fetch_indices_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Connection timeout")
        with self.assertRaises(PSXNetworkError):
            fetch_indices()

    @patch("psx_data.indices.fetch_index_timeseries")
    def test_get_indices(self, mock_fetch):
        mock_fetch.return_value = json.dumps({
            "status": 1,
            "data": [
                [1723507200, 78100.0, 50000],
                [1723507260, 78600.0, 80000],
                [1723507320, 78456.20, 60000],
            ],
        })
        indices = get_indices()
        self.assertGreaterEqual(len(indices), 1)
        self.assertEqual(indices[0].current, 78456.20)

    @patch("psx_data.indices.fetch_index_timeseries")
    def test_get_index_specific(self, mock_fetch):
        mock_fetch.return_value = json.dumps({
            "status": 1,
            "data": [
                [1723507200, 78100.0, 50000],
                [1723507260, 78600.0, 80000],
                [1723507320, 78456.20, 60000],
            ],
        })
        kse100 = get_index("KSE100")
        self.assertIsNotNone(kse100)
        self.assertEqual(kse100.index, "KSE100")
        self.assertEqual(kse100.current, 78456.20)

    @patch("psx_data.indices.fetch_index_timeseries")
    def test_get_index_not_found(self, mock_fetch):
        mock_fetch.return_value = json.dumps({"status": 1, "data": []})
        result = get_index("NON_EXISTING")
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()