from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.error import URLError
from psx_data.exceptions import PSXNetworkError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PSX_BASE_URL = "https://dps.psx.com.pk"
PSX_ANNOUNCEMENTS_URL = f"{PSX_BASE_URL}/announcements"


@dataclass
class Announcement:
    date: str
    time: str
    symbol: str
    name: str
    title: str
    image: str | None
    pdf: str | None

    @property
    def pdf_url(self) -> str | None:
        """Returns the full downloadable URL for the PDF attachment, if available."""
        if not self.pdf:
            return None
        if self.pdf.startswith("http://") or self.pdf.startswith("https://"):
            return self.pdf
        return f"{PSX_BASE_URL}{self.pdf}"

    @property
    def image_urls(self) -> list[str]:
        """Returns a list of full downloadable URLs for image attachments."""
        if not self.image:
            return []
        images = [img.strip() for img in self.image.split(",") if img.strip()]
        return [
            img if img.startswith("http://") or img.startswith("https://")
            else f"{PSX_BASE_URL}/download/image/{img}"
            for img in images
        ]


class _AnnouncementParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.announcements = []

        self._in_row = False
        self._row = []
        self._cell_text = []

        self._image = None
        self._pdf = None
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "tr":
            self._in_row = True
            self._row = []
            self._image = None
            self._pdf = None

        elif tag == "td" and self._in_row:
            self._in_cell = True
            self._cell_text = []

        elif tag == "a" and self._in_row:
            if "data-images" in attrs:
                self._image = attrs["data-images"]

            href = attrs.get("href", "")
            if href.endswith(".pdf"):
                self._pdf = href

    def handle_endtag(self, tag):
        if tag == "td" and self._in_row:
            self._in_cell = False
            self._row.append("".join(self._cell_text).strip())

        elif tag == "tr" and self._in_row:
            self._in_row = False

            if len(self._row) >= 5:
                self.announcements.append(
                    Announcement(
                        date=self._row[0],
                        time=self._row[1],
                        symbol=self._row[2],
                        name=self._row[3],
                        title=self._row[4],
                        image=self._image,
                        pdf=self._pdf,
                    )
                )

    def handle_data(self, data):
        if self._in_cell:
            self._cell_text.append(data)


def parse_announcements(html: str) -> list[Announcement]:
    parser = _AnnouncementParser()
    parser.feed(html)
    return parser.announcements

def get_announcements(
    symbol: str = "",
    count: int = 50,
    offset: int = 0,
    date_from: str = "",
    date_to: str = "",
    timeout: float = 10.0
) -> list[Announcement]:
    html = fetch_announcements(
        symbol=symbol,
        count=count,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        timeout=timeout
    )

    return parse_announcements(html)

def iter_announcements(
    symbol: str = "",
    count: int = 50,
    date_from: str = "",
    date_to: str = "",
    timeout: float = 10.0
):
    offset = 0

    while True:
        announcements = get_announcements(
            symbol=symbol,
            count=count,
            offset=offset,
            date_from=date_from,
            date_to=date_to,
            timeout=timeout
        )

        if not announcements:
            break

        yield from announcements
        offset += count

def fetch_announcements(
    symbol: str = "",
    count: int = 50,
    offset: int = 0,
    date_from: str = "",
    date_to: str = "",
    timeout: float = 10.0
) -> str:
    data = urlencode(
        {
            "type": "C",
            "symbol": symbol,
            "query": "",
            "count": count,
            "offset": offset,
            "date_from": date_from,
            "date_to": date_to,
            "page": "annc",
        }
    ).encode("utf-8")

    request = Request(
        PSX_ANNOUNCEMENTS_URL,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except URLError as e:
        raise PSXNetworkError(f"Failed to fetch announcements: {e}") from e