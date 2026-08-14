import unittest

class TestPackage(unittest.TestCase):

    def test_package_import(self):
        import psx_data

        self.assertIsNotNone(psx_data)

if __name__ == "__main__":
    unittest.main()