"""PSX market and price data (EOD historical OHLCV and Intraday ticks)."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

from psx_data.exceptions import PSXNetworkError, PSXParseError

PSX_BASE_URL = "https://dps.psx.com.pk"


@dataclass
class OHLCV:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int

    @property
    def date_str(self) -> str:
        """Returns ISO date string (YYYY-MM-DD) from timestamp."""
        dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")


@dataclass
class IntradayTick:
    timestamp: int
    price: float
    volume: int

    @property
    def time_str(self) -> str:
        """Returns time string (HH:MM:SS) from timestamp."""
        dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        return dt.strftime("%H:%M:%S")


def _parse_timestamp(val) -> int:
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        val = val.strip()
        if val.isdigit():
            return int(val)
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except (ValueError, TypeError):
            pass
    return 0


def parse_eod(json_str: str) -> list[OHLCV]:
    """Parse JSON string into a list of OHLCV candles."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise PSXParseError(f"Failed to parse EOD JSON: {exc}") from exc

    candles_data = data.get("data", []) if isinstance(data, dict) else data
    if not isinstance(candles_data, list):
        return []

    candles: list[OHLCV] = []
    for item in candles_data:
        if isinstance(item, list):
            try:
                if len(item) >= 6:
                    candles.append(
                        OHLCV(
                            timestamp=_parse_timestamp(item[0]),
                            open=float(item[1]),
                            high=float(item[2]),
                            low=float(item[3]),
                            close=float(item[4]),
                            volume=int(float(item[5])),
                        )
                    )
                elif len(item) == 5:
                    candles.append(
                        OHLCV(
                            timestamp=_parse_timestamp(item[0]),
                            open=float(item[1]),
                            high=float(item[2]),
                            low=float(item[3]),
                            close=float(item[4]),
                            volume=0,
                        )
                    )
                elif len(item) >= 3:
                    p = float(item[1])
                    v = int(float(item[2]))
                    candles.append(
                        OHLCV(
                            timestamp=_parse_timestamp(item[0]),
                            open=p,
                            high=p,
                            low=p,
                            close=p,
                            volume=v,
                        )
                    )
            except (ValueError, TypeError):
                continue
        elif isinstance(item, dict):
            try:
                ts = _parse_timestamp(
                    item.get("timestamp") or item.get("time") or item.get("date", 0)
                )
                o = float(item.get("open", item.get("price", 0)))
                h = float(item.get("high", o))
                l = float(item.get("low", o))
                c = float(item.get("close", o))
                v = int(float(item.get("volume", item.get("vol", 0))))
                candles.append(OHLCV(timestamp=ts, open=o, high=h, low=l, close=c, volume=v))
            except (ValueError, TypeError):
                continue

    return candles


def parse_intraday(json_str: str) -> list[IntradayTick]:
    """Parse JSON string into a list of IntradayTick objects."""
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise PSXParseError(f"Failed to parse Intraday JSON: {exc}") from exc

    ticks_data = data.get("data", []) if isinstance(data, dict) else data
    if not isinstance(ticks_data, list):
        raise PSXParseError("Unexpected Intraday response format, expected list of tick arrays.")

    ticks: list[IntradayTick] = []
    for item in ticks_data:
        if isinstance(item, list) and len(item) >= 3:
            try:
                ticks.append(
                    IntradayTick(
                        timestamp=int(item[0]),
                        price=float(item[1]),
                        volume=int(item[2]),
                    )
                )
            except (ValueError, TypeError):
                continue

    return ticks


def fetch_eod(symbol: str, timeout: float = 10.0) -> str:
    """Fetch raw End-of-Day (EOD) time-series JSON for a stock symbol or index."""
    url = f"{PSX_BASE_URL}/timeseries/eod/{symbol.upper()}"
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
        raise PSXNetworkError(f"Failed to fetch EOD data for {symbol}: {exc}") from exc


def fetch_intraday(symbol: str, timeout: float = 10.0) -> str:
    """Fetch raw Intraday time-series JSON for a stock symbol or index."""
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
        raise PSXNetworkError(f"Failed to fetch Intraday data for {symbol}: {exc}") from exc


def get_eod(
    symbol: str,
    limit: int | None = None,
    timeout: float = 10.0,
) -> list[OHLCV]:
    """Get historical End-of-Day OHLCV candles for a symbol, optionally limiting recent count."""
    raw_json = fetch_eod(symbol=symbol, timeout=timeout)
    candles = parse_eod(raw_json)
    if limit is not None and limit > 0:
        return candles[-limit:]
    return candles


def get_intraday(
    symbol: str,
    limit: int | None = None,
    timeout: float = 10.0,
) -> list[IntradayTick]:
    """Get Intraday price ticks for a symbol, optionally limiting recent count."""
    raw_json = fetch_intraday(symbol=symbol, timeout=timeout)
    ticks = parse_intraday(raw_json)
    if limit is not None and limit > 0:
        return ticks[-limit:]
    return ticks