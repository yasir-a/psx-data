"""Command-line interface for psx-data."""

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

from psx_data import (
    get_announcements,
    get_eod,
    get_intraday,
    get_sectors,
    get_symbols,
)
from psx_data.exceptions import PSXError
from psx_data.storage import download_attachment, export_to_csv


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

    return 0


if __name__ == "__main__":
    sys.exit(main())