import unittest


class TestPackage(unittest.TestCase):

    def test_package_import(self):
        import psx_data

        self.assertIsNotNone(psx_data)

    def test_public_api_import(self):
        from psx_data import Announcement, get_announcements

        self.assertIsNotNone(Announcement)
        self.assertIsNotNone(get_announcements)


if __name__ == "__main__":
    unittest.main()