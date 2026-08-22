# psx-data Features & Usage Guide

`psx-data` is a zero-dependency Python toolkit and CLI for collecting, parsing, and working with Pakistan Stock Exchange (PSX) data.

---

## Table of Contents
- [1. Architecture Overview](#1-architecture-overview)
- [2. Announcements API](#2-announcements-api)
  - [Fetching Announcements](#fetching-announcements)
  - [Auto-Paginating with Generator](#auto-paginating-with-generator)
  - [Data Model & Attachment URLs](#data-model--attachment-urls)
- [3. Symbols & Companies Directory](#3-symbols--companies-directory)
  - [Listing All Tickers & Symbols](#listing-all-tickers--symbols)
  - [Filtering by Sector and Query](#filtering-by-sector-and-query)
  - [Listing Market Sectors](#listing-market-sectors)
- [4. Storage & Export Utilities](#4-storage--export-utilities)
  - [Downloading PDF / Image Attachments](#downloading-pdf--image-attachments)
  - [Exporting to CSV](#exporting-to-csv)
  - [Exporting to JSON](#exporting-to-json)
- [5. Error Handling & Resilience](#5-error-handling--resilience)
- [6. Command-Line Interface (CLI)](#6-command-line-interface-cli)
  - [Announcements Commands](#announcements-commands)
  - [Symbols & Sectors Commands](#symbols--sectors-commands)
  - [Installing and Testing Binary Command](#installing-and-testing-binary-command)
- [7. Test Suite & Quality Assurance](#7-test-suite--quality-assurance)

---

## 1. Architecture Overview

`psx-data` follows a layered, modular architecture with zero third-party runtime dependencies:

```text
PSX Portal (dps.psx.com.pk)
       │
       ▼
Data Collection (HTTP Clients & URL builders)
       │
       ▼
Parsing (HTML streaming parser & JSON parsers)
       │
       ▼
Domain Models (Announcement, Symbol)
       │
 ┌─────┼─────────────┐
 ▼     ▼             ▼
Query Pagination  Storage (download_attachment, export_to_csv, export_to_json)
       │
       ▼
Public API (get_announcements, iter_announcements, get_symbols, get_tickers, get_sectors)
       │
 ┌─────┼─────────────┐
 ▼     ▼             ▼
Python CLI         Web UI (Future)
```

---

## 2. Announcements API

### Fetching Announcements
Fetch a single page of corporate announcements from PSX with filtering support:

```python
from psx_data import get_announcements

# Fetch recent 10 announcements for HUBC
announcements = get_announcements(
    symbol="HUBC",
    count=10,
    date_from="2026-01-01",
    date_to="2026-08-10",
    timeout=10.0,
)

for item in announcements:
    print(f"{item.date} | {item.symbol} | {item.title}")
```

### Auto-Paginating with Generator
Stream all announcements across multiple pages automatically without manually managing offsets:

```python
from psx_data import iter_announcements

for item in iter_announcements(symbol="OGDC", count=50):
    print(f"[{item.date}] {item.title}")
```

### Data Model & Attachment URLs
Each announcement is an `Announcement` dataclass with automatic URL resolution:

* `announcement.date` — Date string (e.g. `"Aug 11, 2026"`)
* `announcement.time` — Time string (e.g. `"3:22 PM"`)
* `announcement.symbol` — Stock ticker symbol (e.g. `"HUBC"`)
* `announcement.name` — Full company name
* `announcement.title` — Announcement subject
* `announcement.pdf_url` — Full absolute download link to PDF document
* `announcement.image_urls` — List of full absolute download links to GIF/PNG notices

---

## 3. Symbols & Companies Directory

### Listing All Tickers & Symbols
Fetch all listed companies on the Pakistan Stock Exchange:

```python
from psx_data import get_symbols, get_tickers

# Get all ticker strings
tickers = get_tickers()
print(tickers[:10])  # ['1847', '786', 'AABS', ...]

# Get structured Symbol objects
symbols = get_symbols()
for s in symbols[:5]:
    print(f"{s.symbol:<8} {s.name} ({s.sector})")
```

### Filtering by Sector and Query
```python
from psx_data import get_symbols

# Filter by market sector
banks = get_symbols(sector="COMMERCIAL BANKS")

# Search by company name or ticker query
power_companies = get_symbols(query="Power")
```

### Listing Market Sectors
```python
from psx_data import get_sectors

sectors = get_sectors()
for sector in sectors:
    print(f"- {sector}")
```

---

## 4. Storage & Export Utilities

### Downloading PDF / Image Attachments
Download official notice attachments directly to a local directory:

```python
from psx_data import get_announcements, download_attachment

announcements = get_announcements(symbol="HUBC", count=5)
for ann in announcements:
    if ann.pdf_url:
        file_path = download_attachment(ann.pdf_url, destination_dir="./downloads")
        print(f"Saved: {file_path}")
```

### Exporting to CSV
Save fetched announcements directly to a CSV file (compatible with Excel & pandas):

```python
from psx_data import get_announcements, export_to_csv

announcements = get_announcements(symbol="HUBC", count=50)
export_to_csv(announcements, "hubc_announcements.csv")
```

### Exporting to JSON
Save announcements to a structured JSON file:

```python
from psx_data import get_announcements, export_to_json

announcements = get_announcements(symbol="SYS", count=20)
export_to_json(announcements, "sys_announcements.json")
```

---

## 5. Error Handling & Resilience

`psx-data` includes a built-in exception hierarchy and configurable network timeouts:

```python
from psx_data import get_announcements
from psx_data.exceptions import PSXError, PSXNetworkError, PSXParseError

try:
    data = get_announcements(symbol="HUBC", timeout=5.0)
except PSXNetworkError as exc:
    print(f"Network failure: {exc}")
except PSXError as exc:
    print(f"General PSX error: {exc}")
```

---

## 6. Command-Line Interface (CLI)

### Announcements Commands

```bash
# 1. Fetch recent announcements (Text output)
psx-data announcements --symbol HUBC --count 5
psx-data announcements --symbol SYS --count 5

# 2. Output in JSON format
psx-data announcements --symbol HUBC --count 2 --json

# 3. Filter by date range
psx-data announcements --symbol OGDC --date-from 2026-01-01 --count 5

# 4. Export announcements to CSV
psx-data announcements --symbol HUBC --count 20 --csv hubc_announcements.csv

# 5. Download all attached PDFs & images directly to a folder
psx-data announcements --symbol HUBC --count 5 --download-dir ./hubc_files
```

### Symbols & Sectors Commands

```bash
# 1. List all active market sectors on PSX
psx-data sectors
# Or via module:
python -m psx_data.cli sectors

# 2. Search companies by query (symbol ticker or company name)
psx-data symbols --query "Power"
psx-data symbols --query "SYS"
# Or via module:
python -m psx_data.cli symbols --query "Power"

# 3. Filter companies by market sector
psx-data symbols --sector "COMMERCIAL BANKS"
# Or via module:
python -m psx_data.cli symbols --sector "COMMERCIAL BANKS"

# 4. Export symbols list to CSV or JSON
psx-data symbols --csv all_symbols.csv
psx-data symbols --query "Bank" --json
# Or via module:
python -m psx_data.cli symbols --csv all_symbols.csv
python -m psx_data.cli symbols --query "Bank" --json
```

### Installing and Testing Binary Command
To install the package locally in editable mode and run the `psx-data` binary directly from anywhere:

```bash
# Install in editable mode
pip install -e .

# Run directly from anywhere in your environment
psx-data --help
psx-data sectors
psx-data symbols --query "OGDC"
psx-data announcements --symbol HUBC --count 5
```

---

## 7. Test Suite & Quality Assurance

* **34 unit tests** using standard library `unittest`.
* Tested against offline PSX HTML and JSON fixtures as well as mock network layers.
* Automated CI pipeline on GitHub Actions.

