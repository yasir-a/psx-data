import unittest


class TestPackage(unittest.TestCase):

    def test_package_import(self):
        import psx_data

        self.assertIsNotNone(psx_data)

    def test_public_api_import(self):
        from psx_data import (
            Announcement,
            PSXError,
            Symbol,
            download_attachment,
            get_announcements,
            get_sectors,
            get_symbols,
            get_tickers,
        )

        self.assertIsNotNone(Announcement)
        self.assertIsNotNone(Symbol)
        self.assertIsNotNone(get_announcements)
        self.assertIsNotNone(get_symbols)
        self.assertIsNotNone(get_tickers)
        self.assertIsNotNone(get_sectors)
        self.assertIsNotNone(download_attachment)
        self.assertIsNotNone(PSXError)


if __name__ == "__main__":
    unittest.main()