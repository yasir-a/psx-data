"""PSX major market indices dashboard (KSE100, KSE30, KMI30, ALLSHR, etc.)."""

import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from psx_data.exceptions import PSXNetworkError, PSXParseError

PSX_BASE_URL = "https://dps.psx.com.pk"

DEFAULT_INDICES = [
    ("KSE100", "KSE 100 Index"),
    ("KSE30", "KSE 30 Index"),
    ("KMI30", "KMI 30 Index (Islamic)"),
    ("ALLSHR", "All Share Index"),
]


@dataclass
class IndexSummary:
    index: str
    name: str
    current: float
    change: float
    percent_change: float
    high: float
    low: float
    volume: int
    status: str = ""


def parse_index_timeseries(index_code: str, index_name: str, json_str: str) -> IndexSummary | None:
    """Parse timeseries JSON for an index and compute current point snapshot."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise PSXParseError(f"Failed to parse index JSON for {index_code}: {exc}") from exc

    ticks = data.get("data", []) if isinstance(data, dict) else data
    if not isinstance(ticks, list) or not ticks:
        return None

    # Ticks format: [timestamp, price, volume]
    prices = []
    total_vol = 0
    for t in ticks:
        if isinstance(t, list) and len(t) >= 2:
            try:
                prices.append(float(t[1]))
                if len(t) >= 3:
                    total_vol += int(float(t[2]))
            except (ValueError, TypeError):
                continue

    if not prices:
        return None

    open_price = prices[0]
    curr_price = prices[-1]
    high_price = max(prices)
    low_price = min(prices)
    change = curr_price - open_price
    pct_change = (change / open_price * 100) if open_price > 0 else 0.0

    return IndexSummary(
        index=index_code.upper(),
        name=index_name,
        current=curr_price,
        change=change,
        percent_change=pct_change,
        high=high_price,
        low=low_price,
        volume=total_vol,
        status="UP" if change >= 0 else "DOWN",
    )


def parse_indices(json_str: str) -> list[IndexSummary]:
    """Parse JSON list of pre-aggregated index records (used for fixtures/custom endpoints)."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise PSXParseError(f"Failed to parse indices JSON: {exc}") from exc

    items = data.get("data", []) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise PSXParseError("Unexpected indices response format, expected list of index records.")

    indices: list[IndexSummary] = []
    for item in items:
        if isinstance(item, dict):
            try:
                idx_name = item.get("index") or item.get("symbol") or item.get("code", "")
                if not idx_name:
                    continue

                curr = float(item.get("current", item.get("val", item.get("value", 0))))
                chg = float(item.get("change", item.get("chg", 0)))
                pct = float(item.get("percent_change", item.get("pct", item.get("percent", 0))))
                hi = float(item.get("high", item.get("hi", curr)))
                lo = float(item.get("low", item.get("lo", curr)))
                vol = int(float(item.get("volume", item.get("vol", 0))))
                name = item.get("name", idx_name)
                status = item.get("status", "UP" if chg >= 0 else "DOWN")

                indices.append(
                    IndexSummary(
                        index=str(idx_name).strip().upper(),
                        name=str(name).strip(),
                        current=curr,
                        change=chg,
                        percent_change=pct,
                        high=hi,
                        low=lo,
                        volume=vol,
                        status=str(status).strip().upper(),
                    )
                )
            except (ValueError, TypeError):
                continue

    return indices


def fetch_index_timeseries(symbol: str, timeout: float = 10.0) -> str:
    """Fetch raw intraday timeseries for an index from PSX."""
    url = f"{PSX_BASE_URL}/timeseries/int/{symbol.upper()}"
    request = Request(
        url,
        headers={
            "User-Agent": "psx-data",
            "X-Requested-With": "XMLHttpRequest",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except URLError as exc:
        raise PSXNetworkError(f"Failed to fetch data for index {symbol}: {exc}") from exc


def fetch_indices(timeout: float = 10.0) -> str:
    """Alias for backwards compatibility and offline mock testing."""
    # When called directly, fetches KSE100 timeseries or returns standard indices
    return fetch_index_timeseries("KSE100", timeout=timeout)


def get_index(symbol: str, timeout: float = 10.0) -> IndexSummary | None:
    """Get snapshot summary for a specific index (e.g. 'KSE100', 'KSE30', 'KMI30', 'ALLSHR')."""
    target = symbol.strip().upper()
    name = dict(DEFAULT_INDICES).get(target, f"{target} Index")

    try:
        raw_json = fetch_index_timeseries(target, timeout=timeout)
        return parse_index_timeseries(target, name, raw_json)
    except PSXNetworkError:
        raise
    except PSXParseError:
        return None


def get_indices(timeout: float = 10.0) -> list[IndexSummary]:
    """Get real-time snapshot of all major PSX benchmark indices."""
    results: list[IndexSummary] = []
    for code, name in DEFAULT_INDICES:
        try:
            raw_json = fetch_index_timeseries(code, timeout=timeout)
            idx_summary = parse_index_timeseries(code, name, raw_json)
            if idx_summary:
                results.append(idx_summary)
        except (PSXNetworkError, PSXParseError):
            continue
    return results