from urllib.parse import parse_qs, urlsplit

import pytest

from photos import street_view_photo_url


def test_photo_url_asks_google_street_view_for_the_address():
    url = street_view_photo_url("12 Brunswick Street, Fitzroy, 3065, Australia", "k1")

    parts = urlsplit(url)
    query = parse_qs(parts.query)
    assert parts.scheme == "https"
    assert parts.netloc == "maps.googleapis.com"
    assert parts.path == "/maps/api/streetview"
    assert query["location"] == ["12 Brunswick Street, Fitzroy, 3065, Australia"]
    assert query["key"] == ["k1"]


def test_photo_url_keeps_an_address_with_reserved_characters_intact():
    url = street_view_photo_url("4/88 King & Queen St #2, Glebe", "k1")

    query = parse_qs(urlsplit(url).query)
    assert query["location"] == ["4/88 King & Queen St #2, Glebe"]
    assert query["key"] == ["k1"]


def test_photo_url_asks_for_an_error_instead_of_the_grey_no_imagery_picture():
    # The card swaps to its placeholder when the image fails to load, which only
    # happens if Google answers 404 where it has no photo.
    url = street_view_photo_url("1 Test St, Sydney", "k1")

    assert parse_qs(urlsplit(url).query)["return_error_code"] == ["true"]


@pytest.mark.parametrize("api_key", [None, ""])
def test_there_is_no_photo_url_without_an_api_key(api_key):
    assert street_view_photo_url("1 Test St, Sydney", api_key) is None
