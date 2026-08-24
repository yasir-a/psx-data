"""Lightweight standard-library HTTP JSON API server for React/Vite UI dashboard."""

import json
import sys
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from psx_data.announcements import get_announcements
from psx_data.companies import get_company_profile
from psx_data.db import (
    get_db_stats,
    query_announcements,
    query_company_profile,
    query_eod,
    query_financials,
    query_symbols,
    save_company_profile,
    save_eod,
    save_financials,
    save_symbols,
)
from psx_data.exceptions import PSXError
from psx_data.financials import get_financials
from psx_data.indices import get_indices
from psx_data.market import get_eod, get_intraday
from psx_data.symbols import get_sectors, get_symbols


class PSXAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler providing REST API endpoints for psx-data frontend."""

    def _set_json_headers(self, status_code: int = 200) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._set_json_headers(204)

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        params = parse_qs(parsed_url.query)

        def get_param(name: str, default: str = "") -> str:
            return params.get(name, [default])[0]

        try:
            if path == "/api/status":
                stats = get_db_stats()
                self._send_json({"status": "ok", "db_stats": stats})

            elif path == "/api/indices":
                indices = get_indices()
                self._send_json({"status": "ok", "data": [asdict(i) for i in indices]})

            elif path == "/api/symbols":
                sector = get_param("sector")
                query = get_param("query")
                from_db = get_param("from_db", "false").lower() == "true"

                if from_db:
                    symbols = query_symbols(sector=sector, query=query)
                else:
                    symbols = get_symbols(sector=sector, query=query)

                self._send_json({"status": "ok", "data": [asdict(s) for s in symbols]})

            elif path == "/api/sectors":
                sectors = get_sectors()
                self._send_json({"status": "ok", "data": sectors})

            elif path == "/api/announcements":
                symbol = get_param("symbol")
                count = int(get_param("count", "20"))
                from_db = get_param("from_db", "false").lower() == "true"

                if from_db:
                    announcements = query_announcements(symbol=symbol, limit=count)
                else:
                    announcements = get_announcements(symbol=symbol, count=count)

                data = [
                    {
                        **asdict(a),
                        "pdf_url": a.pdf_url,
                        "image_urls": a.image_urls,
                    }
                    for a in announcements
                ]
                self._send_json({"status": "ok", "data": data})

            elif path == "/api/eod":
                symbol = get_param("symbol")
                limit = int(get_param("limit", "50"))
                from_db = get_param("from_db", "false").lower() == "true"

                if not symbol:
                    self._send_error(400, "Missing required query parameter: 'symbol'")
                    return

                if from_db:
                    candles = query_eod(symbol=symbol, limit=limit)
                else:
                    candles = get_eod(symbol=symbol, limit=limit)

                data = [{**asdict(c), "date": c.date_str} for c in candles]
                self._send_json({"status": "ok", "symbol": symbol.upper(), "data": data})

            elif path == "/api/intraday":
                symbol = get_param("symbol")
                limit = int(get_param("limit", "50"))

                if not symbol:
                    self._send_error(400, "Missing required query parameter: 'symbol'")
                    return

                ticks = get_intraday(symbol=symbol, limit=limit)
                data = [{**asdict(t), "time": t.time_str} for t in ticks]
                self._send_json({"status": "ok", "symbol": symbol.upper(), "data": data})

            elif path == "/api/company":
                symbol = get_param("symbol")
                from_db = get_param("from_db", "false").lower() == "true"

                if not symbol:
                    self._send_error(400, "Missing required query parameter: 'symbol'")
                    return

                if from_db:
                    profile = query_company_profile(symbol=symbol)
                else:
                    profile = get_company_profile(symbol=symbol)

                if profile:
                    self._send_json({"status": "ok", "data": asdict(profile)})
                else:
                    self._send_error(404, f"No company profile found for symbol '{symbol}'")

            elif path == "/api/financials":
                symbol = get_param("symbol")
                from_db = get_param("from_db", "false").lower() == "true"

                if not symbol:
                    self._send_error(400, "Missing required query parameter: 'symbol'")
                    return

                if from_db:
                    financials = query_financials(symbol=symbol)
                else:
                    financials = get_financials(symbol=symbol)

                data = {
                    "symbol": financials.symbol,
                    "ratios": [asdict(r) for r in financials.ratios],
                    "dividends": [asdict(d) for d in financials.dividends],
                }
                self._send_json({"status": "ok", "data": data})

            else:
                self._send_error(404, f"API endpoint '{path}' not found")

        except PSXError as exc:
            self._send_error(500, f"PSX error: {exc}")
        except Exception as exc:
            self._send_error(500, f"Internal server error: {exc}")

    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            payload = json.loads(body) if body else {}

            if path == "/api/sync/symbols":
                symbols = get_symbols()
                count = save_symbols(symbols)
                self._send_json({"status": "ok", "message": f"Cached {count} symbols to SQLite"})

            elif path == "/api/sync/eod":
                symbol = payload.get("symbol", "").strip().upper()
                limit = int(payload.get("limit", 100))
                if not symbol:
                    self._send_error(400, "Missing 'symbol' in JSON payload")
                    return
                candles = get_eod(symbol=symbol, limit=limit)
                count = save_eod(symbol=symbol, candles=candles)
                self._send_json({"status": "ok", "message": f"Cached {count} candles for {symbol}"})

            elif path == "/api/sync/company":
                symbol = payload.get("symbol", "").strip().upper()
                if not symbol:
                    self._send_error(400, "Missing 'symbol' in JSON payload")
                    return
                profile = get_company_profile(symbol=symbol)
                if profile:
                    save_company_profile(profile)
                    self._send_json({"status": "ok", "message": f"Cached profile for {symbol}"})
                else:
                    self._send_error(404, f"Profile for {symbol} not found")

            elif path == "/api/sync/financials":
                symbol = payload.get("symbol", "").strip().upper()
                if not symbol:
                    self._send_error(400, "Missing 'symbol' in JSON payload")
                    return
                financials = get_financials(symbol=symbol)
                count = save_financials(financials)
                self._send_json({"status": "ok", "message": f"Cached {count} financial records for {symbol}"})

            else:
                self._send_error(404, f"POST endpoint '{path}' not found")

        except Exception as exc:
            self._send_error(500, f"Error processing POST request: {exc}")

    def _send_json(self, data: dict, status_code: int = 200) -> None:
        self._set_json_headers(status_code)
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_error(self, status_code: int, message: str) -> None:
        self._set_json_headers(status_code)
        self.wfile.write(json.dumps({"status": "error", "message": message}).encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write(f"[API Server] {format % args}\n")


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start local API HTTP server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, PSXAPIHandler)
    print(f"--- PSX Data API Server running at http://{host}:{port} ---")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping API server...")
        httpd.server_close()