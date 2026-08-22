"""PSX listed symbols and companies directory."""

import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from psx_data.exceptions import PSXNetworkError, PSXParseError

PSX_SYMBOLS_URL = "https://dps.psx.com.pk/symbols"


@dataclass
class Symbol:
    symbol: str
    name: str
    sector: str = ""


def parse_symbols(json_str: str) -> list[Symbol]:
    """Parse JSON string into a list of Symbol objects."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise PSXParseError(f"Failed to parse symbols JSON: {exc}") from exc

    if not isinstance(data, list):
        raise PSXParseError("Unexpected symbols response format, expected a JSON list.")

    symbols: list[Symbol] = []
    for item in data:
        if isinstance(item, dict):
            sym = item.get("symbol", "").strip()
            name = item.get("name", "").strip()
            sector = item.get("sectorName", "") or item.get("sector", "")
            if sym:
                symbols.append(
                    Symbol(
                        symbol=sym,
                        name=name,
                        sector=sector.strip(),
                    )
                )

    return symbols


def fetch_symbols(timeout: float = 10.0) -> str:
    """Fetch raw symbols JSON from PSX Data Portal."""
    request = Request(
        PSX_SYMBOLS_URL,
        headers={
            "User-Agent": "psx-data",
            "X-Requested-With": "XMLHttpRequest",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except URLError as exc:
        raise PSXNetworkError(f"Failed to fetch symbols from PSX: {exc}") from exc


def get_symbols(
    sector: str = "",
    query: str = "",
    timeout: float = 10.0,
) -> list[Symbol]:
    """Get all listed symbols with optional sector or search query filtering."""
    raw_json = fetch_symbols(timeout=timeout)
    symbols = parse_symbols(raw_json)

    if sector:
        target_sector = sector.strip().upper()
        symbols = [s for s in symbols if s.sector.upper() == target_sector]

    if query:
        target_query = query.strip().upper()
        symbols = [
            s for s in symbols
            if target_query in s.symbol.upper() or target_query in s.name.upper()
        ]

    return symbols


def get_tickers(timeout: float = 10.0) -> list[str]:
    """Get a simple list of all stock ticker symbols."""
    symbols = get_symbols(timeout=timeout)
    return [s.symbol for s in symbols]


def get_sectors(timeout: float = 10.0) -> list[str]:
    """Get a sorted list of all unique sectors on PSX."""
    symbols = get_symbols(timeout=timeout)
    sectors = {s.sector for s in symbols if s.sector}
    return sorted(sectors)