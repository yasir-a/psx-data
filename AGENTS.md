# AGENTS.md — Development & Operating Instructions for AI Agents

> **Persistent Context Document**  
> This file is the primary source of truth and operating guidance for AI coding agents working on `psx-data`. Read this document before inspecting or modifying the codebase.

---

## 1. Project Overview

* **Project Name**: `psx-data`
* **Purpose**: An open-source, zero-dependency Python toolkit and command-line interface (CLI) for collecting, parsing, and working with data from the Pakistan Stock Exchange (PSX Data Portal: `dps.psx.com.pk`).
* **Goals**:
  * Provide clean, typed, and structured Python data models for PSX corporate announcements, listed company symbols/sectors, historical end-of-day (EOD) OHLCV candles, and real-time intraday ticks.
  * Provide a feature-rich CLI for terminal users and shell scripting.
  * Adhere strictly to a **zero-dependency philosophy** by using only Python's standard library.
  * Maintain comprehensive test coverage using unit tests with offline HTML/JSON fixtures and mock network layers.
  * Provide a local SQLite caching layer for offline access to persisted data.
  * Long-term: serve data to a **React + Vite frontend UI**.
* **Current Scope**: Corporate Announcements, Symbols & Sectors Directory, EOD & Intraday Market Data, Market Indices Dashboard, SQLite Local Storage & Cache, Attachment Downloads (PDFs/Images), and Data Exporters (CSV/JSON).

---

## 2. Architecture & Data Flow

`psx-data` implements a layered, unidirectional data-pipeline architecture:

```text
       ┌────────────────────────────────────────────────────────┐
       │             PSX Data Portal (dps.psx.com.pk)           │
       └───────────────────────────┬────────────────────────────┘
                                   │ HTTP GET / POST
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Layer 2: Data Collection & Network Layer               │
       │ (urllib.request, urllib.parse, timeouts, URLError map) │
       └───────────────────────────┬────────────────────────────┘
                                   │ Raw HTML / JSON strings
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Layer 3: Parsing Layer                                 │
       │ (html.parser.HTMLParser streaming, json decoding)      │
       └───────────────────────────┬────────────────────────────┘
                                   │ Structured attributes / tokens
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Layer 4: Domain Models (Typed dataclasses)             │
       │ (Announcement, Symbol, OHLCV, IntradayTick)            │
       └───────────────────────────┬────────────────────────────┘
                                   │
                     ┌─────────────┼─────────────┐
                     ▼             ▼             ▼
             ┌──────────────┐┌──────────────┐┌──────────────────────┐
             │ Query/Filter ││  Pagination  ││ Storage & Exporters  │
             │ (Date/Sector)││ (Generators) ││ (CSV/JSON/Downloads) │
             └───────┬──────┘└──────┬───────┘└──────────┬───────────┘
                     └─────────────┼─────────────┘
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Layer 6: Public API Facade (psx_data/__init__.py)      │
       └───────────────────────────┬────────────────────────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
       ┌───────────────────────────┐ ┌───────────────────────────┐
       │ Layer 7a: Python SDK      │ │ Layer 7b: CLI             │
       │ (import psx_data)         │ │ (psx_data/cli.py)         │
       └───────────────────────────┘ └───────────────────────────┘
```

### Major Modules & Responsibilities

| Module | Location | Responsibility |
| :--- | :--- | :--- |
| **Public API** | [`src/psx_data/__init__.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/__init__.py) | Facade exporting all domain dataclasses, high-level client functions, exceptions, and storage helpers. |
| **Announcements** | [`src/psx_data/announcements.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/announcements.py) | Scrapes `dps.psx.com.pk/announcements` via POST requests; parses table HTML with `_AnnouncementParser(HTMLParser)`; yields `Announcement` dataclasses with `pdf_url` and `image_urls` properties; provides `get_announcements` and `iter_announcements` generator. |
| **Symbols** | [`src/psx_data/symbols.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/symbols.py) | Fetches `dps.psx.com.pk/symbols`; parses JSON into `Symbol` objects; provides `get_symbols`, `get_tickers`, and `get_sectors` with filtering. |
| **Market Data** | [`src/psx_data/market.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/market.py) | Fetches time-series data: EOD historical candles from `/timeseries/eod/{SYMBOL}` into `OHLCV`, and real-time intraday ticks from `/timeseries/int/{SYMBOL}` into `IntradayTick`. |
| **Indices** | [`src/psx_data/indices.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/indices.py) | Real-time tracking of benchmark indices (`KSE100`, `KSE30`, `KMI30`, `ALLSHR`, etc.). |
| **Company Profiles** | [`src/psx_data/companies.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/companies.py) | Scrapes listed company profiles, market cap, shares listed, free float, and management info (`get_company_profile`). |
| **Financials & Ratios** | [`src/psx_data/financials.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/financials.py) | Scrapes and parses financial ratios (EPS, P/E, ROE, BV) and dividend payout history (`get_financials`). |
| **SQLite Storage** | [`src/psx_data/db.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/db.py) | Relational caching and persistence layer (`init_db`, `save_symbols`, `query_symbols`, `save_announcements`, `query_announcements`, `save_eod`, `query_eod`, `save_company_profile`, `query_company_profile`, `save_financials`, `query_financials`, `get_db_stats`). |
| **Local REST API** | [`src/psx_data/server.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/server.py) | Stdlib HTTP JSON API server (`run_server`) bridge for UI dashboard. |
| **Storage & Export** | [`src/psx_data/storage.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/storage.py) | Downloads PDF/image attachments (`download_attachment`); exports records to CSV (`export_to_csv`) and JSON (`export_to_json`). |
| **Exceptions** | [`src/psx_data/exceptions.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/exceptions.py) | Custom exception hierarchy: `PSXError` (base), `PSXNetworkError`, `PSXParseError`. |
| **CLI** | [`src/psx_data/cli.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/cli.py) | Entry point `main(argv)` supporting subcommands: `announcements`, `symbols`, `sectors`, `indices`, `eod`, `intraday`, `company`, `financials`, `db`, and `serve`. |

---

## 3. Repository Structure

```text
psx-data/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md      # Template for all pull requests
│   └── workflows/
│       └── tests.yml                 # GitHub Actions CI workflow (Python 3.11, ubuntu-latest)
├── docs/
│   └── FEATURES.md                   # Comprehensive feature guide and live CLI command examples
├── src/
│   └── psx_data/
│       ├── __init__.py               # Top-level public package exports
│       ├── announcements.py          # Corporate announcements scraper & parser
│       ├── cli.py                    # Command-line interface entry point
│       ├── companies.py              # Company profiles and fundamentals parser
│       ├── db.py                     # SQLite local persistence and caching layer
│       ├── exceptions.py             # Custom exceptions hierarchy
│       ├── financials.py             # Financial statements, ratios & dividend history
│       ├── indices.py                # Major market indices dashboard (KSE100, KSE30, KMI30, ALLSHR)
│       ├── market.py                 # EOD historical OHLCV & Intraday ticks
│       ├── server.py                 # Stdlib HTTP JSON API server bridge
│       ├── storage.py                # Attachment downloader & CSV/JSON exporters
│       └── symbols.py                # Listed companies & market sectors directory
├── tests/
│   ├── fixtures/
│   │   ├── announcements_hubc.html   # Offline HTML fixture for announcement parser
│   │   ├── company_hubc.html         # Offline HTML fixture for company profile parser
│   │   ├── eod_hubc.json             # Offline JSON fixture for EOD candles
│   │   ├── financials_hubc.html      # Offline HTML fixture for financials parser
│   │   ├── indices.json              # Offline JSON fixture for indices
│   │   ├── intraday_hubc.json        # Offline JSON fixture for intraday ticks
│   │   └── symbols.json              # Offline JSON fixture for listed symbols
│   ├── test_announcements.py         # Announcements unit & pagination tests
│   ├── test_cli.py                   # CLI subcommands & argument parsing tests
│   ├── test_companies.py             # Company profiles unit tests
│   ├── test_db.py                    # SQLite storage unit tests (uses temp file, not mocks)
│   ├── test_financials.py            # Financials & ratios unit tests
│   ├── test_indices.py               # Indices parser/fetcher tests
│   ├── test_market.py                # Market EOD & Intraday parser/fetcher tests
│   ├── test_package.py               # Package & public API import verification tests
│   ├── test_storage.py               # File downloads & CSV/JSON export tests
│   └── test_symbols.py               # Symbols, tickers, and sectors tests
├── ui/                               # React 19 + Vite + TypeScript frontend dashboard
├── .gitignore
├── AGENTS.md                         # This file (AI developer handoff and persistent context)
├── CHANGELOG.md                      # Release changelog following SemVer
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md                   # Contribution rules and branching strategy
├── LICENSE                           # MIT License
├── pyproject.toml                    # Setuptools build configuration & CLI script entry point
├── README.md                         # Project overview and roadmap
└── SECURITY.md                       # Security vulnerability policy
```

---

## 4. Technology Stack & Environment

* **Language**: Python 3.11+ (typed, modern dataclasses, union syntax `str | None`).
* **Runtime Dependencies**: **None**. Zero external runtime dependencies. Only Python Standard Library (`urllib`, `html.parser`, `dataclasses`, `datetime`, `json`, `csv`, `sqlite3`, `http.server`, `pathlib`, `argparse`, `sys`).
* **Build System**: `setuptools>=68` configured via [`pyproject.toml`](file:///c:/Users/yasir/projects/psx-data/pyproject.toml) using a `src/` layout.
* **CLI Entry Point**: `psx-data = "psx_data.cli:main"` registered in `[project.scripts]`.
* **Virtual Environment**: `.venv/` at the project root. Always activate before running tests or CLI commands:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  Or run directly:
  ```powershell
  .\.venv\Scripts\python.exe -m unittest discover -s tests -v
  ```
* **Testing Framework**: Python standard `unittest` with `unittest.mock` (offline execution with fixtures, no external network requests during tests). `test_db.py` uses `tempfile.TemporaryDirectory` for real SQLite isolation — all connections must be explicitly `.close()`d before `tearDown` to avoid Windows file-lock errors.
* **CI/CD**: GitHub Actions running on `ubuntu-latest` with Python 3.11 (`python -m unittest discover -s tests -v`).

---

## 5. Development Rules & Coding Conventions

1. **Zero External Dependencies**:
   * Do NOT add third-party dependencies (such as `requests`, `beautifulsoup4`, `pandas`, `pydantic`, or `click`) without explicit user discussion and approval. All scraping, parsing, data modeling, and CLI functionality must remain standard-library-based.
2. **Type Annotations**:
   * All public functions, methods, and dataclass fields must have clear Python type annotations (e.g. `timeout: float = 10.0`, `symbol: str = ""`, `limit: int | None = None`).
3. **Resilience & Error Handling**:
   * Network calls must specify explicit `timeout` arguments (default `10.0` seconds).
   * Map standard `urllib.error.URLError` to `PSXNetworkError`.
   * Map JSON/HTML parsing anomalies to `PSXParseError`.
   * Keep raw stack traces from bubbling to the CLI; handlers should catch `PSXError`, print to `sys.stderr`, and return non-zero exit codes.
4. **Data Normalization & Helpers**:
   * Models should provide convenient properties for relative URLs (e.g. `announcement.pdf_url`, `announcement.image_urls`) and formatted timestamps (`candle.date_str`, `tick.time_str`).
   * Parsers must handle inconsistent types (e.g. float volumes, integer timestamps, ISO strings, missing array items) gracefully.

---

## 6. Architecture Constraints

* **Preserve the `src/` layout**: All application code lives inside `src/psx_data/`.
* **Preserve `__all__` in `src/psx_data/__init__.py`**: Every new domain model or high-level function must be explicitly exposed in `__all__` and tested in [`tests/test_package.py`](file:///c:/Users/yasir/projects/psx-data/tests/test_package.py).
* **Do NOT execute live network calls inside unit tests**: All unit tests must use `unittest.mock.patch` against network functions or read from static offline fixtures in `tests/fixtures/`.
* **Do NOT modify user workspace or run git mutating commands autonomously**: The human developer operates git commands and repository modifications outside documentation. Agents guide the developer with exact code snippets, diffs, and commands.

---

## 7. Strict Git & Branching Workflow

Every feature, fix, or refactor must follow the 22-step workflow established in `CONTRIBUTING.md`:

```text
1. Never develop directly on main.
2. Start from an up-to-date main:
     git switch main
     git pull origin main
3. Create a dedicated branch:
     git switch -c feature/<description>  (or fix/, test/, docs/, refactor/)
4. Test-Driven Development (TDD):
     Write/update tests -> Run tests (expect failure) -> Implement code -> Run full test suite.
5. Verify working tree before staging:
     git status
     git diff
     git diff --check
6. Stage specific files only (never blindly git add .):
     git add src/psx_data/... tests/... docs/...
7. Commit using conventional format:
     feat: <description>
     fix: <description>
     docs: <description>
     test: <description>
8. Push feature branch:
     git push -u origin feature/<description>
9. Open Pull Request to main using .github/PULL_REQUEST_TEMPLATE.md.
10. Ensure GitHub Actions CI passes.
11. Merge PR on GitHub.
12. Sync and clean up local main:
     git switch main
     git pull origin main
     git branch -d feature/<description>
     git push origin --delete feature/<description>
```

---

## 8. Testing Instructions

* **Run complete test suite** (activate venv first):
  ```powershell
  .\.venv\Scripts\python.exe -m unittest discover -s tests -v
  ```
* **Run specific test file**:
  ```powershell
  .\.venv\Scripts\python.exe -m unittest tests/test_announcements.py -v
  .\.venv\Scripts\python.exe -m unittest tests/test_companies.py -v
  .\.venv\Scripts\python.exe -m unittest tests/test_financials.py -v
  .\.venv\Scripts\python.exe -m unittest tests/test_market.py -v
  .\.venv\Scripts\python.exe -m unittest tests/test_symbols.py -v
  .\.venv\Scripts\python.exe -m unittest tests/test_storage.py -v
  .\.venv\Scripts\python.exe -m unittest tests/test_cli.py -v
  .\.venv\Scripts\python.exe -m unittest tests/test_indices.py -v
  .\.venv\Scripts\python.exe -m unittest tests/test_db.py -v
  ```
* **Windows SQLite note**: All `sqlite3` connections opened in tests must call `.close()` explicitly (not just rely on context manager) before `tearDown`'s `tempfile.TemporaryDirectory.cleanup()` runs, to avoid `PermissionError: [WinError 32]` file-lock errors.
* **Verification rule**: The entire test suite (**currently 77 tests**) must pass with `OK` before opening any PR or concluding a task.

---

## 9. Current Implementation Status & Roadmap

### Completed Features (Verified & Tested)
* ✅ **Corporate Announcements Client** ([`src/psx_data/announcements.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/announcements.py)): Single-page fetch, streaming generator pagination (`iter_announcements`), date/symbol filtering, `pdf_url` and `image_urls` property resolvers.
* ✅ **Symbols & Sectors Directory** ([`src/psx_data/symbols.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/symbols.py)): Listed tickers, company names, market sectors, query substring search, and sector listing.
* ✅ **Market & Price Data** ([`src/psx_data/market.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/market.py)): Historical EOD OHLCV daily bars (`get_eod`) and real-time Intraday ticks (`get_intraday`). Resilient `parse_eod` handles float volumes and variable-length timeseries arrays.
* ✅ **Major Market Indices Dashboard** ([`src/psx_data/indices.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/indices.py)): Real-time tracking of benchmark indices (`KSE100`, `KSE30`, `KMI30`, `ALLSHR`) via `/timeseries/int/{INDEX}` endpoint; computes open/high/low/close/volume from intraday ticks.
* ✅ **Company Fundamentals & Profiles** ([`src/psx_data/companies.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/companies.py)): Listed shares, market cap, executive leadership (CEO, Chairman, Auditor), and corporate profile metadata (`get_company_profile`).
* ✅ **Financial Statements, Ratios & Dividends** ([`src/psx_data/financials.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/financials.py)): Scrapes and parses annual & quarterly financial metrics (EPS, Gross Profit Margin %, Net Profit Margin %, EPS Growth %, PEG) and dividend payout history (`get_financials`).
* ✅ **Local SQLite Storage Layer** ([`src/psx_data/db.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/db.py)): Relational caching via `sqlite3` (`init_db`, `save_symbols`, `query_symbols`, `save_announcements`, `query_announcements`, `save_eod`, `query_eod`, `save_company_profile`, `query_company_profile`, `save_financials`, `query_financials`, `get_db_stats`).
* ✅ **Local REST API Server** ([`src/psx_data/server.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/server.py)): Stdlib HTTP server serving JSON endpoints to the UI dashboard.
* ✅ **React + Vite Frontend Web UI** (`ui/`): Modern dashboard in React 19 + TypeScript + Tailwind CSS with live indices ticker, symbol explorer, price charts, company profile cards, and SQLite cache manager.
* ✅ **CLI Interface** ([`src/psx_data/cli.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/cli.py)): Subcommands `announcements`, `symbols`, `sectors`, `indices`, `eod`, `intraday`, `company`, `financials`, `db`, and `serve`.
* ✅ **Error Handling** ([`src/psx_data/exceptions.py`](file:///c:/Users/yasir/projects/psx-data/src/psx_data/exceptions.py)): Custom exceptions with network timeout wrappers.
* ✅ **Feature Documentation** ([`docs/FEATURES.md`](file:///c:/Users/yasir/projects/psx-data/docs/FEATURES.md)): Comprehensive guide with tested live CLI examples.

### Pending Roadmap Items
* ⏳ **Financial Statements / Ratio Analysis (`src/psx_data/financials.py`)**: Balance sheets, income statements, and dividend histories.
* ⏳ **Release `v0.2.0` Prep**: Updating `CHANGELOG.md`, `pyproject.toml`, and creating git release tags.


---

## 10. AI Agent Operating Instructions

When taking over tasks on this repository, future AI agents must adhere to these directives:

1. **Read `AGENTS.md` and `docs/FEATURES.md` first**: Always verify existing patterns and architecture before generating code.
2. **Act as a Guide**: Do not execute modifying shell commands or modify source files directly unless specifically authorized by the user. Provide exact file paths, line numbers, code snippets, diffs, and verification commands.
3. **Maintain `docs/FEATURES.md` and `AGENTS.md`**: When adding a new feature module, update `docs/FEATURES.md` with usage examples and update `AGENTS.md` when architectural decisions or component statuses change.
4. **Follow TDD**: Write tests with offline fixtures in `tests/` first, ensure expected failure, implement the feature, and ensure all unit tests pass before handing off.
5. **No Hallucinated Endpoints**: Base all network integrations on verified PSX Data Portal (`dps.psx.com.pk`) endpoints.

