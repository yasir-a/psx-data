"""Financial statements, key financial ratios, and dividend payout history parser."""

from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import Request, urlopen

from psx_data.exceptions import PSXNetworkError, PSXParseError

PSX_BASE_URL = "https://dps.psx.com.pk"


@dataclass
class DividendRecord:
    symbol: str
    announcement_date: str = ""
    financial_year_end: str = ""
    dividend_percent: float = 0.0
    dividend_amount: float = 0.0
    bonus_percent: float = 0.0
    right_percent: float = 0.0


@dataclass
class FinancialRatio:
    symbol: str
    period: str = ""
    eps: float = 0.0
    gross_margin: float = 0.0
    net_margin: float = 0.0
    eps_growth: float = 0.0
    peg_ratio: float = 0.0
    pe_ratio: float = 0.0
    book_value: float = 0.0
    dividend_yield: float = 0.0
    roe: float = 0.0


@dataclass
class FinancialSummary:
    symbol: str
    ratios: list[FinancialRatio] = field(default_factory=list)
    dividends: list[DividendRecord] = field(default_factory=list)


class _FinancialsParser(HTMLParser):
    """HTML parser to extract ratios and dividend tables from PSX company/financials markup."""

    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.symbol = symbol.upper()
        self.ratios: list[FinancialRatio] = []
        self.dividends: list[DividendRecord] = []

        self._current_section = ""
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._is_header_row = False
        self._current_row_cells: list[str] = []
        self._current_cell_text = ""

        # Multi-year column matrix storage for PSX layout (years in columns)
        self._table_headers: list[str] = []
        self._metrics: dict[str, list[float]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        elem_id = attr_dict.get("id", "").lower()

        if tag == "div" and elem_id in ("financials", "ratios", "payouts"):
            self._current_section = elem_id

        if tag == "table":
            self._in_table = True
            self._table_headers = []
            self._metrics = {}

        elif tag == "tr" and self._in_table:
            self._in_row = True
            self._is_header_row = False
            self._current_row_cells = []

        elif tag in ("td", "th") and self._in_row:
            self._in_cell = True
            self._current_cell_text = ""
            if tag == "th":
                self._is_header_row = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._in_cell:
            self._in_cell = False
            self._current_row_cells.append(self._current_cell_text.strip())

        elif tag == "tr" and self._in_row:
            self._in_row = False
            self._process_row()

        elif tag == "table":
            self._in_table = False
            self._finalize_column_matrix()

        elif tag == "div" and self._current_section:
            pass

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell_text += data

    def _process_row(self) -> None:
        cells = self._current_row_cells
        if not cells:
            return

        def parse_float(val: str) -> float:
            cleaned = (
                val.replace("%", "")
                .replace(",", "")
                .replace(" ", "")
                .replace("PKR", "")
                .replace("Rs.", "")
                .replace("(", "-")
                .replace(")", "")
                .strip()
            )
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

        if self._is_header_row:
            # Check if header row contains years (e.g. 2025, 2024, Q3 2026)
            year_headers = [c for c in cells if any(char.isdigit() for char in c)]
            if year_headers:
                self._table_headers = [c for c in cells if c]
            return

        first_col = cells[0].strip()
        first_col_lower = first_col.lower()

        # Check if first cell is a date (e.g. '2024-08-15', 'Apr 29, 2026', '15/08/2024')
        is_date = (
            ("-" in first_col or "/" in first_col or any(m in first_col_lower for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]))
            and any(char.isdigit() for char in first_col)
            and not any(term in first_col_lower for term in ["margin", "sales", "profit", "eps", "peg", "growth"])
        )

        # 1. Dividend / Payout Row
        if is_date and len(cells) >= 3:
            date_str = first_col
            year_end = cells[1].strip() if len(cells) > 1 else ""
            div_pct = parse_float(cells[2]) if len(cells) > 2 else 0.0
            div_amt = parse_float(cells[3]) if len(cells) > 3 else 0.0
            bonus_pct = parse_float(cells[4]) if len(cells) > 4 else 0.0
            right_pct = parse_float(cells[5]) if len(cells) > 5 else 0.0

            if div_pct > 0 or div_amt > 0 or bonus_pct > 0 or right_pct > 0:
                self.dividends.append(
                    DividendRecord(
                        symbol=self.symbol,
                        announcement_date=date_str,
                        financial_year_end=year_end,
                        dividend_percent=div_pct,
                        dividend_amount=div_amt,
                        bonus_percent=bonus_pct,
                        right_percent=right_pct,
                    )
                )
            return

        # 2. Row-Oriented Ratio Row (Period is first col e.g. "FY 2024", "FY23")
        if first_col_lower.startswith("fy") and len(cells) >= 3:
            period = first_col
            eps = parse_float(cells[1]) if len(cells) > 1 else 0.0
            pe = parse_float(cells[2]) if len(cells) > 2 else 0.0
            bv = parse_float(cells[3]) if len(cells) > 3 else 0.0
            roe = parse_float(cells[4]) if len(cells) > 4 else 0.0
            dy = parse_float(cells[5]) if len(cells) > 5 else 0.0

            self.ratios.append(
                FinancialRatio(
                    symbol=self.symbol,
                    period=period,
                    eps=eps,
                    pe_ratio=pe,
                    book_value=bv,
                    roe=roe,
                    dividend_yield=dy,
                )
            )
            return

        # 3. Column-Oriented Matrix (Row label is metric e.g. "EPS", "Profit after Taxation", "Gross Profit Margin")
        metric_name = first_col_lower
        values = [parse_float(c) for c in cells[1:]]
        if values:
            self._metrics[metric_name] = values
    
    def _finalize_column_matrix(self) -> None:
        """Convert collected column-oriented metrics into FinancialRatio records."""
        if not self._table_headers or not self._metrics:
            return

        eps_list = self._metrics.get("eps", [])
        gross_list = self._metrics.get("gross profit margin (%)", self._metrics.get("gross profit margin", []))
        net_list = self._metrics.get("net profit margin (%)", self._metrics.get("net profit margin", []))
        growth_list = self._metrics.get("eps growth (%)", self._metrics.get("eps growth", []))
        peg_list = self._metrics.get("peg", [])

        for idx, header in enumerate(self._table_headers):
            period = header.strip()
            if not period:
                continue

            eps = eps_list[idx] if idx < len(eps_list) else 0.0
            gross = gross_list[idx] if idx < len(gross_list) else 0.0
            net = net_list[idx] if idx < len(net_list) else 0.0
            growth = growth_list[idx] if idx < len(growth_list) else 0.0
            peg = peg_list[idx] if idx < len(peg_list) else 0.0

            if eps != 0.0 or gross != 0.0 or net != 0.0 or growth != 0.0 or peg != 0.0:
                existing = next((r for r in self.ratios if r.period == period), None)
                if existing:
                    if eps:
                        existing.eps = eps
                    if gross:
                        existing.gross_margin = gross
                    if net:
                        existing.net_margin = net
                    if growth:
                        existing.eps_growth = growth
                    if peg:
                        existing.peg_ratio = peg
                else:
                    self.ratios.append(
                        FinancialRatio(
                            symbol=self.symbol,
                            period=period,
                            eps=eps,
                            gross_margin=gross,
                            net_margin=net,
                            eps_growth=growth,
                            peg_ratio=peg,
                        )
                    )

def parse_ratios(symbol: str, html_str: str) -> list[FinancialRatio]:
    """Parse financial ratio table rows from HTML."""
    parser = _FinancialsParser(symbol)
    try:
        parser.feed(html_str)
        return parser.ratios
    except Exception as exc:
        raise PSXParseError(f"Failed to parse ratios for {symbol}: {exc}") from exc


def parse_dividends(symbol: str, html_str: str) -> list[DividendRecord]:
    """Parse dividend payout history from HTML."""
    parser = _FinancialsParser(symbol)
    try:
        parser.feed(html_str)
        return parser.dividends
    except Exception as exc:
        raise PSXParseError(f"Failed to parse dividends for {symbol}: {exc}") from exc


def parse_financials(symbol: str, html_str: str) -> FinancialSummary:
    """Parse combined financial summary (ratios and dividends) for a symbol."""
    parser = _FinancialsParser(symbol)
    try:
        parser.feed(html_str)
        return FinancialSummary(
            symbol=symbol.upper(),
            ratios=parser.ratios,
            dividends=parser.dividends,
        )
    except Exception as exc:
        raise PSXParseError(f"Failed to parse financials for {symbol}: {exc}") from exc


def fetch_financials(symbol: str, timeout: float = 10.0) -> str:
    """Fetch raw HTML for company financials from PSX Data Portal."""
    url = f"{PSX_BASE_URL}/company/{symbol.upper()}"
    request = Request(
        url,
        headers={
            "User-Agent": "psx-data",
            "X-Requested-With": "XMLHttpRequest",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except URLError as exc:
        raise PSXNetworkError(f"Failed to fetch financials for {symbol}: {exc}") from exc


def get_financials(symbol: str, timeout: float = 10.0) -> FinancialSummary:
    """Fetch and return combined FinancialSummary for a given stock symbol."""
    html_str = fetch_financials(symbol=symbol, timeout=timeout)
    return parse_financials(symbol=symbol, html_str=html_str)