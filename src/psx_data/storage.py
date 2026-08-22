"""Storage and export utilities for psx-data."""

import csv
import json
from dataclasses import asdict
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from psx_data.announcements import Announcement
from psx_data.exceptions import PSXError, PSXNetworkError


def download_attachment(
    url: str,
    destination_dir: str | Path,
    filename: str | None = None,
    timeout: float = 10.0,
) -> Path:
    """Download an attachment (PDF or image) from a given URL to a destination directory.

    Returns the Path to the downloaded file.
    """
    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        parsed = urlparse(url)
        filename = Path(parsed.path).name or "download"

    target_file = dest_dir / filename

    request = Request(
        url,
        headers={
            "User-Agent": "psx-data",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            target_file.write_bytes(response.read())
    except URLError as exc:
        raise PSXNetworkError(f"Failed to download attachment from {url}: {exc}") from exc
    except OSError as exc:
        raise PSXError(f"Failed to write attachment to {target_file}: {exc}") from exc

    return target_file


def export_to_csv(
    announcements: list[Announcement],
    filepath: str | Path,
) -> Path:
    """Export a list of Announcement objects to a CSV file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "date",
        "time",
        "symbol",
        "name",
        "title",
        "pdf_url",
        "image_urls",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ann in announcements:
            writer.writerow(
                {
                    "date": ann.date,
                    "time": ann.time,
                    "symbol": ann.symbol,
                    "name": ann.name,
                    "title": ann.title,
                    "pdf_url": ann.pdf_url or "",
                    "image_urls": ";".join(ann.image_urls),
                }
            )

    return path


def export_to_json(
    announcements: list[Announcement],
    filepath: str | Path,
    indent: int = 2,
) -> Path:
    """Export a list of Announcement objects to a JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = [
        {
            **asdict(ann),
            "pdf_url": ann.pdf_url,
            "image_urls": ann.image_urls,
        }
        for ann in announcements
    ]

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)

    return path