"""Company fundamentals and profile scraper for Pakistan Stock Exchange."""

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import Request, urlopen

from psx_data.exceptions import PSXNetworkError, PSXParseError

PSX_BASE_URL = "https://dps.psx.com.pk"


@dataclass
class CompanyProfile:
    symbol: str
    name: str = ""
    sector: str = ""
    shares_listed: int = 0
    free_float: int = 0
    market_cap: float = 0.0
    ceo: str = ""
    chairperson: str = ""
    auditor: str = ""
    website: str = ""
    address: str = ""
    fiscal_year_end: str = ""


class _CompanyProfileParser(HTMLParser):
    """HTML parser to extract company metadata from PSX company page."""

    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.symbol = symbol.upper()
        self.name = ""
        self.sector = ""
        self.shares_listed = 0
        self.free_float = 0
        self.market_cap = 0.0
        self.ceo = ""
        self.chairperson = ""
        self.auditor = ""
        self.website = ""
        self.address = ""
        self.fiscal_year_end = ""

        # Parser state
        self._in_row = False
        self._in_cell = False
        self._row_cells: list[str] = []
        self._current_cell_text = ""

        self._in_stats_label = False
        self._in_stats_value = False
        self._in_item_head = False
        self._in_item_p = False

        self._last_stats_label = ""
        self._last_head = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        classes = attr_dict.get("class", "").split()
        classes_str = attr_dict.get("class", "").lower()
        if tag in ("div", "h1", "span"):
            if "quote__name" in classes or "company__name" in classes or tag == "h1":
                self._in_item_head = True
                self._last_head = "company_name"
                self._current_cell_text = ""
            elif "quote__sector" in classes or "company__sector" in classes:
                self._in_item_head = True
                self._last_head = "company_sector"
                self._current_cell_text = ""
            elif "stats_label" in classes or "label" in classes:
                self._in_stats_label = True
                self._current_cell_text = ""
            elif "stats_value" in classes or "value" in classes:
                self._in_stats_value = True
                self._current_cell_text = ""
            elif "item__head" in classes:
                self._in_item_head = True
                self._current_cell_text = ""
        elif tag == "p":
            self._in_item_p = True
            self._current_cell_text = ""
        elif tag == "tr":
            self._in_row = True
            self._row_cells = []
        elif tag in ("td", "th") and self._in_row:
            self._in_cell = True
            self._current_cell_text = ""
        elif tag == "a" and self._last_head == "website":
            href = attr_dict.get("href", "")
            if href and "http" in href:
                self.website = href

    def handle_endtag(self, tag: str) -> None:
        text = self._current_cell_text.strip()
        if tag in ("div", "h1", "span"):
            if self._in_stats_label:
                self._in_stats_label = False
                self._last_stats_label = text.lower()
            elif self._in_stats_value:
                self._in_stats_value = False
                self._process_stats_value(text)
            elif self._in_item_head:
                self._in_item_head = False
                if self._last_head == "company_name" and text:
                    if not self.name:
                        self.name = text
                    self._last_head = ""
                elif self._last_head == "company_sector" and text:
                    if not self.sector:
                        self.sector = text
                    self._last_head = ""
                else:
                    self._last_head = text.lower()
        elif tag == "p" and self._in_item_p:
            self._in_item_p = False
            self._process_item_p(text)
        elif tag in ("td", "th") and self._in_cell:
            self._in_cell = False
            self._row_cells.append(text)
        elif tag == "tr" and self._in_row:
            self._in_row = False
            self._process_table_row()

    def handle_data(self, data: str) -> None:
        if self._in_cell or self._in_stats_label or self._in_stats_value or self._in_item_head or self._in_item_p:
            self._current_cell_text += data

    def _process_stats_value(self, text: str) -> None:
        label = self._last_stats_label
        clean_num = text.replace(",", "").replace("Rs.", "").replace("PKR", "").strip()

        if "market cap" in label and not self.market_cap:
            try:
                self.market_cap = float(clean_num)
            except ValueError:
                pass
        elif "shares" in label and not self.shares_listed:
            try:
                self.shares_listed = int(float(clean_num))
            except ValueError:
                pass
        elif "free float" in label and not self.free_float and "%" not in text:
            try:
                self.free_float = int(float(clean_num))
            except ValueError:
                pass

    def _process_item_p(self, text: str) -> None:
        head = self._last_head
        if "auditor" in head and not self.auditor:
            self.auditor = text
        elif "address" in head and not self.address:
            self.address = text
        elif "website" in head and not self.website:
            self.website = text
        elif "fiscal" in head and not self.fiscal_year_end:
            self.fiscal_year_end = text

    def _process_table_row(self) -> None:
        cells = self._row_cells
        if len(cells) >= 2:
            # Table format: Name in cells[0], Title/Role in cells[1]
            # or Label in cells[0], Value in cells[1]
            first = cells[0].strip()
            second = cells[1].strip()

            second_lower = second.lower()
            if second_lower == "ceo" or "chief executive" in second_lower:
                self.ceo = first
            elif "chair" in second_lower or "chairman" in second_lower:
                self.chairperson = first

            first_lower = first.lower()
            if "chief executive" in first_lower or first_lower == "ceo":
                self.ceo = second
            elif "chair" in first_lower or "chairman" in first_lower:
                self.chairperson = second
            elif "auditor" in first_lower and not self.auditor:
                self.auditor = second
            elif "website" in first_lower and not self.website:
                self.website = second
            elif "address" in first_lower and not self.address:
                self.address = second

    def to_profile(self) -> CompanyProfile:
        return CompanyProfile(
            symbol=self.symbol,
            name=self.name or self.symbol,
            sector=self.sector,
            shares_listed=self.shares_listed,
            free_float=self.free_float,
            market_cap=self.market_cap,
            ceo=self.ceo,
            chairperson=self.chairperson,
            auditor=self.auditor,
            website=self.website,
            address=self.address,
            fiscal_year_end=self.fiscal_year_end,
        )

def parse_company_profile(symbol: str, html_str: str) -> CompanyProfile:
    """Parse HTML string of PSX company page into a CompanyProfile dataclass."""
    parser = _CompanyProfileParser(symbol)
    try:
        parser.feed(html_str)
        return parser.to_profile()
    except Exception as exc:
        raise PSXParseError(f"Failed to parse company profile for {symbol}: {exc}") from exc


def fetch_company_profile(symbol: str, timeout: float = 10.0) -> str:
    """Fetch raw HTML for a company profile from PSX Data Portal."""
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
        raise PSXNetworkError(f"Failed to fetch company profile for {symbol}: {exc}") from exc


def get_company_profile(symbol: str, timeout: float = 10.0) -> CompanyProfile | None:
    """Fetch and return structured CompanyProfile for a given stock symbol."""
    html_str = fetch_company_profile(symbol=symbol, timeout=timeout)
    return parse_company_profile(symbol=symbol, html_str=html_str)