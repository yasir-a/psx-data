import unittest


class TestPackage(unittest.TestCase):

    def test_package_import(self):
        import psx_data

        self.assertIsNotNone(psx_data)

    def test_public_api_import(self):
        from psx_data import (
            IndexSummary,
            OHLCV,
            Announcement,
            IntradayTick,
            PSXError,
            Symbol,
            download_attachment,
            get_announcements,
            get_eod,
            get_index,
            get_indices,
            get_intraday,
            get_sectors,
            get_symbols,
            get_tickers,
            init_db,
            query_announcements,
            query_eod,
            query_symbols,
            save_announcements,
            save_eod,
            save_symbols,
            CompanyProfile, 
            get_company_profile, 
            save_company_profile, 
            query_company_profile,
            DividendRecord,
            FinancialRatio,
            FinancialSummary,
            get_financials,
            save_financials,
            query_financials,
            
        )

        self.assertIsNotNone(Announcement)
        self.assertIsNotNone(Symbol)
        self.assertIsNotNone(OHLCV)
        self.assertIsNotNone(IntradayTick)
        self.assertIsNotNone(IndexSummary)
        self.assertIsNotNone(init_db)
        self.assertIsNotNone(save_symbols)
        self.assertIsNotNone(query_symbols)
        self.assertIsNotNone(save_announcements)
        self.assertIsNotNone(query_announcements)
        self.assertIsNotNone(save_eod)
        self.assertIsNotNone(query_eod)
        self.assertIsNotNone(get_announcements)
        self.assertIsNotNone(get_symbols)
        self.assertIsNotNone(get_tickers)
        self.assertIsNotNone(get_sectors)
        self.assertIsNotNone(get_eod)
        self.assertIsNotNone(get_intraday)
        self.assertIsNotNone(get_indices)
        self.assertIsNotNone(get_index)
        self.assertIsNotNone(download_attachment)
        self.assertIsNotNone(PSXError)
        self.assertIsNotNone(CompanyProfile)
        self.assertIsNotNone(get_company_profile)
        self.assertIsNotNone(save_company_profile)
        self.assertIsNotNone(query_company_profile)
        self.assertIsNotNone(DividendRecord)
        self.assertIsNotNone(FinancialRatio)
        self.assertIsNotNone(FinancialSummary)
        self.assertIsNotNone(get_financials)
        self.assertIsNotNone(save_financials)
        self.assertIsNotNone(query_financials)


if __name__ == "__main__":
    unittest.main()