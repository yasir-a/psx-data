"""Command-line interface for psx-data."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from psx_data import get_announcements
from psx_data.exceptions import PSXError
from psx_data.storage import download_attachment, export_to_csv, export_to_json


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

    # Export to CSV if requested
    if args.csv:
        csv_path = export_to_csv(announcements, args.csv)
        print(f"Saved {len(announcements)} announcements to {csv_path}")

    # Download attachments if requested
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

    # Output format
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "announcements":
        return handle_announcements(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())