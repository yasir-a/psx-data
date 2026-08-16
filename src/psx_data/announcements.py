from urllib.parse import urlencode
from urllib.request import Request, urlopen


PSX_ANNOUNCEMENTS_URL = "https://dps.psx.com.pk/announcements"


def fetch_announcements(
    symbol: str = "",
    count: int = 50,
    offset: int = 0,
    date_from: str = "",
    date_to: str = "",
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

    with urlopen(request) as response:
        return response.read().decode("utf-8")