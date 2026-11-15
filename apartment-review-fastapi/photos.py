from typing import Optional
from urllib.parse import urlencode

_STREET_VIEW_URL = "https://maps.googleapis.com/maps/api/streetview"


def street_view_photo_url(address: str, api_key: Optional[str]) -> Optional[str]:
    """
    Address of a Google Street View photo of the building, for an <img> tag.

    The visitor's browser loads the photo straight from Google: Google's terms do
    not allow keeping a copy. Returns None when no API key is configured.
    """
    if not api_key:
        return None

    query = urlencode(
        {
            "size": "640x400",
            "location": address,
            # Street-level photos only, not the inside of a shop next door
            "source": "outdoor",
            # 404 instead of a grey "no imagery" picture, so the page can tell
            "return_error_code": "true",
            "key": api_key,
        }
    )
    return f"{_STREET_VIEW_URL}?{query}"
