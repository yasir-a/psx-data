# Changelog

All notable changes to psx-data will be documented in this file.

The project follows [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-08-24

### Added
- **Company Fundamentals & Profiles** (`src/psx_data/companies.py`):
  - Company metadata scraper and parser (`get_company_profile`, `fetch_company_profile`, `parse_company_profile`).
  - Extracted fields: CEO, Chairperson, Company Secretary, Auditor, Registrar, business description, address, website, shares listed, free float, and market cap.
  - CLI subcommand: `psx-data company --symbol HUBC [--json] [--save]`.
- **Financial Statements, Ratios & Dividends** (`src/psx_data/financials.py`):
  - Scrapes and parses annual & quarterly financial metrics (EPS, Gross Margin %, Net Margin %, EPS Growth %, PEG).
  - Scrapes and parses dividend/payout history (cash dividend %, amount, bonus %, right shares %).
  - CLI subcommand: `psx-data financials --symbol HUBC [--json] [--save]`.
- **Local SQLite Persistence Layer** (`src/psx_data/db.py`):
  - Relational caching with standard `sqlite3` with zero external dependencies.
  - Schema tables for `symbols`, `announcements`, `eod_candles`, `company_profiles`, `financial_ratios`, and `dividends`.
  - Database status reporter: `get_db_stats()`.
  - CLI subcommands: `psx-data db init`, `psx-data db status`, `psx-data db sync-symbols`, `psx-data db sync-eod`.
- **Lightweight Stdlib REST API Server** (`src/psx_data/server.py`):
  - Built-in HTTP server (`run_server`) serving JSON API endpoints (`/api/status`, `/api/indices`, `/api/symbols`, `/api/sectors`, `/api/announcements`, `/api/eod`, `/api/intraday`, `/api/company`, `/api/financials`, and `/api/sync/*`).
  - CLI subcommand: `psx-data serve --port 8000`.
- **React + Vite Frontend Web Dashboard** (`ui/`):
  - Modern web dashboard built with React 19, TypeScript, and Tailwind CSS.
  - Live benchmark indices ticker, interactive symbol explorer, price chart visualizations, company fundamental profile cards, and SQLite database cache manager.
- Comprehensive unit test suite with 77 offline fixture and mock tests.

## [0.1.0] - 2026-08-16

### Added
- Initial open-source project structure
- Python package structure
- Automated test workflow with GitHub Actions
- Contribution guidelines
- Code of Conduct
- Security Policy
- GitHub issue templates
- Pull Request template