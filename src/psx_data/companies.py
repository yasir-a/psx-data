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
        self._current_tag = ""
        self._current_classes: list[str] = []
        self._in_table_cell = False
        self._last_label = ""
        self._text_buffer = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._current_tag = tag
        attr_dict = dict(attrs)
        classes = attr_dict.get("class", "").split()
        self._current_classes = classes
        self._text_buffer = ""

        if tag in ("td", "span", "div", "h1"):
            self._in_table_cell = True

    def handle_endtag(self, tag: str) -> None:
        text = self._text_buffer.strip()

        if "company__name" in self._current_classes or tag == "h1":
            if text and not self.name:
                self.name = text
        elif "company__sector" in self._current_classes:
            if text and not self.sector:
                self.sector = text

        # Handle key-value table rows
        if self._last_label:
            cleaned_label = self._last_label.lower().replace(":", "").strip()
            if "chief executive" in cleaned_label or cleaned_label == "ceo":
                self.ceo = text
            elif "chairman" in cleaned_label or "chairperson" in cleaned_label:
                self.chairperson = text
            elif "auditor" in cleaned_label:
                self.auditor = text
            elif "website" in cleaned_label or "url" in cleaned_label:
                self.website = text
            elif "address" in cleaned_label:
                self.address = text
            elif "fiscal" in cleaned_label:
                self.fiscal_year_end = text
            elif "shares" in cleaned_label:
                try:
                    self.shares_listed = int(text.replace(",", "").replace(" ", ""))
                except ValueError:
                    pass
            elif "free float" in cleaned_label:
                try:
                    self.free_float = int(text.replace(",", "").replace(" ", ""))
                except ValueError:
                    pass
            elif "market cap" in cleaned_label:
                try:
                    self.market_cap = float(text.replace(",", "").replace(" ", ""))
                except ValueError:
                    pass
            self._last_label = ""
        elif text.endswith(":") or any(
            k in text.lower()
            for k in [
                "chief executive",
                "chairman",
                "auditor",
                "website",
                "address",
                "fiscal",
                "shares",
                "free float",
                "market cap",
            ]
        ):
            self._last_label = text

        self._in_table_cell = False

    def handle_data(self, data: str) -> None:
        if self._in_table_cell:
            self._text_buffer += data

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