# psx-data Features & Usage Guide

`psx-data` is a zero-dependency Python toolkit and CLI for collecting, parsing, and working with Pakistan Stock Exchange (PSX) data.

---

## Table of Contents
- [1. Architecture Overview](#1-architecture-overview)
- [2. Announcements API](#2-announcements-api)
  - [Fetching Announcements](#fetching-announcements)
  - [Auto-Paginating with Generator](#auto-paginating-with-generator)
  - [Data Model & Attachment URLs](#data-model--attachment-urls)
- [3. Storage & Export Utilities](#3-storage--export-utilities)
  - [Downloading PDF / Image Attachments](#downloading-pdf--image-attachments)
  - [Exporting to CSV](#exporting-to-csv)
  - [Exporting to JSON](#exporting-to-json)
- [4. Error Handling & Resilience](#4-error-handling--resilience)
- [5. Command-Line Interface (CLI)](#5-command-line-interface-cli)
  - [Available CLI Commands & Examples](#available-cli-commands--examples)
  - [Exporting & Downloading via CLI](#exporting--downloading-via-cli)
  - [Installing and Testing the Binary Command](#installing-and-testing-the-binary-command)
- [6. Test Suite & Quality Assurance](#6-test-suite--quality-assurance)

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
Parsing (HTML streaming parser)
       │
       ▼
Domain Models (Announcement dataclass)
       │
 ┌─────┼─────────────┐
 ▼     ▼             ▼
Query Pagination  Storage (download_attachment, export_to_csv, export_to_json)
       │
       ▼
Public API (get_announcements, iter_announcements, storage utilities)
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

## 3. Storage & Export Utilities

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

## 4. Error Handling & Resilience

`psx-data` includes a built-in exception hierarchy and configurable network timeouts:

```python
from psx_data import get_announcements
from psx_data.exceptions import PSXError, PSXNetworkError

try:
    data = get_announcements(symbol="HUBC", timeout=5.0)
except PSXNetworkError as exc:
    print(f"Network failure: {exc}")
except PSXError as exc:
    print(f"General PSX error: {exc}")
```

---

## 5. Command-Line Interface (CLI)

### Available CLI Commands & Examples

```bash
# 1. View general help menu
python -m psx_data.cli --help

# 2. View announcements subcommand options
python -m psx_data.cli announcements --help

# 3. Fetch recent announcements for a company (Text output)
python -m psx_data.cli announcements --symbol HUBC --count 5
python -m psx_data.cli announcements --symbol SYS --count 5

# 4. Fetch announcements in JSON format
python -m psx_data.cli announcements --symbol HUBC --count 2 --json

# 5. Filter announcements by date range
python -m psx_data.cli announcements --symbol OGDC --date-from 2026-01-01 --count 5
```

### Exporting & Downloading via CLI

```bash
# Export announcements to CSV
python -m psx_data.cli announcements --symbol HUBC --count 20 --csv hubc_announcements.csv

# Download all PDF & image notices directly to a folder
python -m psx_data.cli announcements --symbol HUBC --count 5 --download-dir ./hubc_files
```

### Installing and Testing the Binary Command
To install the package locally in editable mode and run the `psx-data` binary directly:

```bash
# Install in editable mode
pip install -e .

# Run the CLI binary directly from anywhere in your environment
psx-data announcements --symbol HUBC --count 5
psx-data announcements --symbol SYS --count 5
psx-data announcements --symbol HUBC --csv hubc.csv
```

---

## 6. Test Suite & Quality Assurance

* **24 unit tests** using standard library `unittest`.
* Tested against offline PSX HTML fixtures and mock network layers.
* Automated CI pipeline on GitHub Actions.
