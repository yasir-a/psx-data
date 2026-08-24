"""Command-line interface for psx-data."""

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

from psx_data.announcements import get_announcements, iter_announcements
from psx_data.companies import get_company_profile
from psx_data.db import (
    DEFAULT_DB_PATH,
    get_db_stats,
    init_db,
    save_company_profile,
    save_eod,
    save_financials,
    save_symbols,
)
from psx_data.exceptions import PSXError
from psx_data.financials import get_financials
from psx_data.indices import get_index, get_indices
from psx_data.market import get_eod, get_intraday
from psx_data.server import run_server
from psx_data.storage import download_attachment, export_to_csv, export_to_json
from psx_data.symbols import get_sectors, get_symbols


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psx-data",
        description="CLI toolkit for Pakistan Stock Exchange (PSX) data",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: announcements
    ann_parser = subparsers.add_parser(
        "announcements",
        help="Fetch corporate announcements from PSX",
    )
    ann_parser.add_argument(
        "--symbol",
        "-s",
        type=str,
        default="",
        help="Filter by stock ticker symbol (e.g. HUBC, OGDC)",
    )
    ann_parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=20,
        help="Number of announcements to fetch (default: 20)",
    )
    ann_parser.add_argument(
        "--date-from",
        type=str,
        default="",
        help="Start date filter (YYYY-MM-DD)",
    )
    ann_parser.add_argument(
        "--date-to",
        type=str,
        default="",
        help="End date filter (YYYY-MM-DD)",
    )
    ann_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format to stdout",
    )
    ann_parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="Save results to a CSV file path",
    )
    ann_parser.add_argument(
        "--download-dir",
        type=str,
        default="",
        help="Directory to download associated PDF and image attachments",
    )

    # Subcommand: symbols
    sym_parser = subparsers.add_parser(
        "symbols",
        help="List and search listed stock symbols and companies",
    )
    sym_parser.add_argument(
        "--sector",
        type=str,
        default="",
        help="Filter by sector name (e.g. 'COMMERCIAL BANKS')",
    )
    sym_parser.add_argument(
        "--query",
        "-q",
        type=str,
        default="",
        help="Search query to match symbol or company name",
    )
    sym_parser.add_argument(
        "--json",
        action="store_true",
        help="Output symbols in JSON format",
    )
    sym_parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="Save symbols list to a CSV file",
    )

    # Subcommand: sectors
    subparsers.add_parser(
        "sectors",
        help="List all active market sectors on PSX",
    )

    # Subcommand: eod
    eod_parser = subparsers.add_parser(
        "eod",
        help="Fetch historical End-of-Day (EOD) OHLCV candles",
    )
    eod_parser.add_argument(
        "--symbol",
        "-s",
        type=str,
        required=True,
        help="Stock ticker symbol or index (e.g. HUBC, SYS, KSE100)",
    )
    eod_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=20,
        help="Number of recent daily candles to display (default: 20)",
    )
    eod_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    eod_parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="Save candles to a CSV file path",
    )

    # Subcommand: intraday
    int_parser = subparsers.add_parser(
        "intraday",
        help="Fetch real-time intraday price ticks",
    )
    int_parser.add_argument(
        "--symbol",
        "-s",
        type=str,
        required=True,
        help="Stock ticker symbol or index (e.g. HUBC, SYS, KSE100)",
    )
    int_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=20,
        help="Number of recent intraday ticks to display (default: 20)",
    )
    int_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    int_parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="Save ticks to a CSV file path",
    )

    # Subcommand: indices
    idx_parser = subparsers.add_parser(
        "indices",
        help="Fetch major PSX benchmark indices (KSE100, KSE30, KMI30, ALLSHR, etc.)",
    )
    idx_parser.add_argument(
        "--symbol",
        "-s",
        type=str,
        default="",
        help="Filter for a specific index symbol (e.g. KSE100)",
    )
    idx_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    idx_parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="Save indices to a CSV file path",
    )

    # Subcommand: db
    db_parser = subparsers.add_parser(
        "db",
        help="Manage local SQLite cache and database storage",
    )
    db_subparsers = db_parser.add_subparsers(dest="db_action", required=True)

    # Action: init
    db_init_parser = db_subparsers.add_parser("init", help="Initialize SQLite database tables")
    db_init_parser.add_argument(
        "--db",
        type=str,
        default=str(DEFAULT_DB_PATH),
        help=f"Database file path (default: {DEFAULT_DB_PATH})",
    )

    # Action: status
    db_status_parser = db_subparsers.add_parser("status", help="Show SQLite database statistics")
    db_status_parser.add_argument(
        "--db",
        type=str,
        default=str(DEFAULT_DB_PATH),
        help=f"Database file path (default: {DEFAULT_DB_PATH})",
    )

    # Action: sync-symbols
    db_sync_sym_parser = db_subparsers.add_parser(
        "sync-symbols",
        help="Fetch all symbols from PSX and cache in SQLite",
    )
    db_sync_sym_parser.add_argument(
        "--db",
        type=str,
        default=str(DEFAULT_DB_PATH),
        help=f"Database file path (default: {DEFAULT_DB_PATH})",
    )

    # Action: sync-eod
    db_sync_eod_parser = db_subparsers.add_parser(
        "sync-eod",
        help="Fetch EOD candles for a symbol and cache in SQLite",
    )
    db_sync_eod_parser.add_argument(
        "--symbol",
        "-s",
        type=str,
        required=True,
        help="Stock ticker symbol (e.g. HUBC, SYS)",
    )
    db_sync_eod_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=100,
        help="Number of EOD candles to fetch and cache (default: 100)",
    )
    db_sync_eod_parser.add_argument(
        "--db",
        type=str,
        default=str(DEFAULT_DB_PATH),
        help=f"Database file path (default: {DEFAULT_DB_PATH})",
    )

        # Subcommand: company
    comp_parser = subparsers.add_parser(
        "company",
        help="Fetch company fundamentals and profile (CEO, shares, market cap)",
    )
    comp_parser.add_argument(
        "--symbol",
        "-s",
        type=str,
        required=True,
        help="Stock ticker symbol (e.g. HUBC, SYS, OGDC)",
    )
    comp_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    comp_parser.add_argument(
        "--save",
        action="store_true",
        help="Cache profile into local SQLite database",
    )

        # Subcommand: financials
    fin_parser = subparsers.add_parser(
        "financials",
        help="Fetch key financial ratios, EPS, P/E, and dividend payout history",
    )
    fin_parser.add_argument(
        "--symbol",
        "-s",
        type=str,
        required=True,
        help="Stock ticker symbol (e.g. HUBC, SYS, OGDC)",
    )
    fin_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    fin_parser.add_argument(
        "--save",
        action="store_true",
        help="Save financials into local SQLite database",
    )

    # Subcommand: serve
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start local REST API HTTP server for frontend UI",
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface to bind to (default: 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port number to listen on (default: 8000)",
    )

    return parser


def handle_announcements(args: argparse.Namespace) -> int:
    try:
        announcements = get_announcements(
            symbol=args.symbol,
            count=args.count,
            date_from=args.date_from,
            date_to=args.date_to,
        )
    except PSXError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not announcements:
        print("No announcements found.")
        return 0

    if args.csv:
        csv_path = export_to_csv(announcements, args.csv)
        print(f"Saved {len(announcements)} announcements to {csv_path}")

    if args.download_dir:
        dest = Path(args.download_dir)
        download_count = 0
        for ann in announcements:
            if ann.pdf_url:
                try:
                    download_attachment(ann.pdf_url, dest)
                    download_count += 1
                except PSXError as exc:
                    print(f"Warning: Failed to download {ann.pdf_url}: {exc}", file=sys.stderr)
            for img_url in ann.image_urls:
                try:
                    download_attachment(img_url, dest)
                    download_count += 1
                except PSXError as exc:
                    print(f"Warning: Failed to download {img_url}: {exc}", file=sys.stderr)
        print(f"Downloaded {download_count} attachments to {dest}")

    if args.json:
        data = [
            {
                **asdict(ann),
                "pdf_url": ann.pdf_url,
                "image_urls": ann.image_urls,
            }
            for ann in announcements
        ]
        print(json.dumps(data, indent=2))
        return 0

    if not args.csv and not args.download_dir:
        for ann in announcements:
            pdf_info = f" [PDF: {ann.pdf_url}]" if ann.pdf_url else ""
            print(f"[{ann.date} {ann.time}] {ann.symbol} - {ann.title}{pdf_info}")

    return 0


def handle_symbols(args: argparse.Namespace) -> int:
    try:
        symbols = get_symbols(sector=args.sector, query=args.query)
    except PSXError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not symbols:
        print("No symbols found matching the criteria.")
        return 0

    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol", "name", "sector"])
            writer.writeheader()
            for s in symbols:
                writer.writerow(asdict(s))
        print(f"Saved {len(symbols)} symbols to {csv_path}")
        return 0

    if args.json:
        print(json.dumps([asdict(s) for s in symbols], indent=2))
        return 0

    for s in symbols:
        sector_str = f" ({s.sector})" if s.sector else ""
        print(f"{s.symbol:<8} {s.name}{sector_str}")

    return 0


def handle_sectors() -> int:
    try:
        sectors = get_sectors()
    except PSXError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for sector in sectors:
        print(f"- {sector}")

    return 0


def handle_eod(args: argparse.Namespace) -> int:
    try:
        candles = get_eod(symbol=args.symbol, limit=args.limit)
    except PSXError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not candles:
        print(f"No EOD data found for symbol '{args.symbol}'.")
        return 0

    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["date", "timestamp", "open", "high", "low", "close", "volume"]
            )
            writer.writeheader()
            for c in candles:
                writer.writerow({**asdict(c), "date": c.date_str})
        print(f"Saved {len(candles)} candles to {csv_path}")
        return 0

    if args.json:
        data = [{**asdict(c), "date": c.date_str} for c in candles]
        print(json.dumps(data, indent=2))
        return 0

    print(f"--- EOD Historical Quotes: {args.symbol.upper()} ---")
    print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>14}")
    for c in candles:
        print(
            f"{c.date_str:<12} {c.open:>10.2f} {c.high:>10.2f} {c.low:>10.2f} "
            f"{c.close:>10.2f} {c.volume:>14,d}"
        )

    return 0


def handle_intraday(args: argparse.Namespace) -> int:
    try:
        ticks = get_intraday(symbol=args.symbol, limit=args.limit)
    except PSXError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not ticks:
        print(f"No Intraday data found for symbol '{args.symbol}'.")
        return 0

    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["time", "timestamp", "price", "volume"])
            writer.writeheader()
            for t in ticks:
                writer.writerow({**asdict(t), "time": t.time_str})
        print(f"Saved {len(ticks)} ticks to {csv_path}")
        return 0

    if args.json:
        data = [{**asdict(t), "time": t.time_str} for t in ticks]
        print(json.dumps(data, indent=2))
        return 0

    print(f"--- Intraday Price Ticks: {args.symbol.upper()} ---")
    print(f"{'Time':<10} {'Price':>10} {'Volume':>14}")
    for t in ticks:
        print(f"{t.time_str:<10} {t.price:>10.2f} {t.volume:>14,d}")

    return 0


def handle_indices(args: argparse.Namespace) -> int:
    try:
        if args.symbol:
            idx = get_index(args.symbol)
            indices = [idx] if idx else []
        else:
            indices = get_indices()
    except PSXError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not indices:
        msg = f"No index found for symbol '{args.symbol}'." if args.symbol else "No indices found."
        print(msg)
        return 0

    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "index",
                    "name",
                    "current",
                    "change",
                    "percent_change",
                    "high",
                    "low",
                    "volume",
                    "status",
                ],
            )
            writer.writeheader()
            for item in indices:
                writer.writerow(asdict(item))
        print(f"Saved {len(indices)} indices to {csv_path}")
        return 0

    if args.json:
        print(json.dumps([asdict(i) for i in indices], indent=2))
        return 0

    print(f"{'Index':<10} {'Current':>12} {'Change':>10} {'% Change':>10} {'High':>12} {'Low':>12} {'Volume':>14}")
    print("-" * 84)
    for i in indices:
        print(
            f"{i.index:<10} {i.current:>12.2f} {i.change:>+10.2f} {i.percent_change:>+9.2f}% "
            f"{i.high:>12.2f} {i.low:>12.2f} {i.volume:>14,d}"
        )

    return 0

def handle_db(args: argparse.Namespace) -> int:
    db_path = Path(args.db)

    if args.db_action == "init":
        path = init_db(db_path)
        print(f"Initialized SQLite database at: {path.resolve()}")
        return 0

    elif args.db_action == "status":
        stats = get_db_stats(db_path)
        print(f"--- Database Status: {db_path} ---")
        print(f"Symbols:        {stats.get('symbols', 0):,}")
        print(f"Announcements:  {stats.get('announcements', 0):,}")
        print(f"EOD Candles:    {stats.get('eod_candles', 0):,}")
        return 0

    elif args.db_action == "sync-symbols":
        try:
            symbols = get_symbols()
            count = save_symbols(symbols, db_path=db_path)
            print(f"Successfully cached {count} symbols to {db_path}")
            return 0
        except PSXError as exc:
            print(f"Error syncing symbols: {exc}", file=sys.stderr)
            return 1

    elif args.db_action == "sync-eod":
        try:
            candles = get_eod(symbol=args.symbol, limit=args.limit)
            if not candles:
                print(f"No EOD data found for '{args.symbol}' to cache.")
                return 0
            count = save_eod(symbol=args.symbol, candles=candles, db_path=db_path)
            print(f"Successfully cached {count} EOD candles for {args.symbol.upper()} to {db_path}")
            return 0
        except PSXError as exc:
            print(f"Error syncing EOD data: {exc}", file=sys.stderr)
            return 1

    return 0

def handle_company(args: argparse.Namespace) -> int:
    try:
        profile = get_company_profile(args.symbol)
    except PSXError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not profile:
        print(f"No company profile found for symbol '{args.symbol}'.")
        return 0

    if args.save:
        save_company_profile(profile)
        print(f"Cached profile for {profile.symbol} to SQLite database.")

    if args.json:
        print(json.dumps(asdict(profile), indent=2))
        return 0

    print(f"=== {profile.symbol} - {profile.name} ===")
    if profile.sector:
        print(f"Sector:          {profile.sector}")
    if profile.market_cap:
        print(f"Market Cap:      PKR {profile.market_cap:,.2f}")
    if profile.shares_listed:
        print(f"Shares Listed:   {profile.shares_listed:,}")
    if profile.free_float:
        print(f"Free Float:      {profile.free_float:,}")
    if profile.ceo:
        print(f"CEO:             {profile.ceo}")
    if profile.chairperson:
        print(f"Chairperson:     {profile.chairperson}")
    if profile.auditor:
        print(f"Auditor:         {profile.auditor}")
    if profile.website:
        print(f"Website:         {profile.website}")
    if profile.address:
        print(f"Address:         {profile.address}")
    if profile.fiscal_year_end:
        print(f"Fiscal Year End: {profile.fiscal_year_end}")

    return 0

def handle_financials(args: argparse.Namespace) -> int:
    try:
        financials = get_financials(args.symbol)
    except PSXError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not financials.ratios and not financials.dividends:
        print(f"No financials or dividend records found for '{args.symbol}'.")
        return 0

    if args.save:
        count = save_financials(financials)
        print(f"Cached {count} financial records for {financials.symbol} to SQLite database.")

    if args.json:
        data = {
            "symbol": financials.symbol,
            "ratios": [asdict(r) for r in financials.ratios],
            "dividends": [asdict(d) for d in financials.dividends],
        }
        print(json.dumps(data, indent=2))
        return 0

    if financials.ratios:
        print(f"=== Financial Ratios & Margins: {financials.symbol} ===")
        print(f"{'Period':<12} {'EPS (PKR)':>12} {'Gross Margin':>15} {'Net Margin':>15} {'EPS Growth':>15} {'PEG':>10}")
        print("-" * 83)
        for r in financials.ratios:
            gross_str = f"{r.gross_margin:.2f}%" if r.gross_margin else "—"
            net_str = f"{r.net_margin:.2f}%" if r.net_margin else "—"
            growth_str = f"{r.eps_growth:+.2f}%" if r.eps_growth else "—"
            peg_str = f"{r.peg_ratio:.2f}" if r.peg_ratio else "—"
            print(
                f"{r.period:<12} {r.eps:>12.2f} {gross_str:>15} {net_str:>15} {growth_str:>15} {peg_str:>10}"
            )
        print()

    if financials.dividends:
        print(f"=== Dividend & Payout History: {financials.symbol} ===")
        print(f"{'Date':<14} {'Year End':<14} {'Div %':>8} {'Amount (PKR)':>14} {'Bonus %':>10} {'Right %':>10}")
        print("-" * 74)
        for d in financials.dividends:
            print(
                f"{d.announcement_date:<14} {d.financial_year_end:<14} {d.dividend_percent:>7.1f}% "
                f"{d.dividend_amount:>14.2f} {d.bonus_percent:>9.1f}% {d.right_percent:>9.1f}%"
            )

    return 0

def handle_serve(args: argparse.Namespace) -> int:
    try:
        run_server(host=args.host, port=args.port)
        return 0
    except Exception as exc:
        print(f"Error running API server: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "announcements":
        return handle_announcements(args)
    elif args.command == "symbols":
        return handle_symbols(args)
    elif args.command == "sectors":
        return handle_sectors()
    elif args.command == "eod":
        return handle_eod(args)
    elif args.command == "intraday":
        return handle_intraday(args)
    elif args.command == "indices":
        return handle_indices(args)
    elif args.command == "db":
        return handle_db(args)
    elif args.command == "company":
        return handle_company(args)
    elif args.command == "financials":
        return handle_financials(args)
    elif args.command == "serve":
        return handle_serve(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())