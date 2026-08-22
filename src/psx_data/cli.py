"""Command-line interface for psx-data."""

import argparse
import json
import sys
from dataclasses import asdict

from psx_data import get_announcements
from psx_data.exceptions import PSXError


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
        help="Output results in JSON format",
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

    if not announcements:
        print("No announcements found.")
        return 0

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