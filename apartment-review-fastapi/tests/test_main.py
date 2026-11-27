from models import Apartment


def test_create_apartment_returns_response(client):
    response = client.post(
        "/apartment",
        json={
            "city": "Sydney",
            "country": "Australia",
            "country_code": "AU",
            "display_name": "1 Test St, Sydney, Australia",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Sydney"
    assert "uid" in body
    assert "latitude" not in body
    assert "longitude" not in body


def test_create_apartment_rejects_missing_city(client):
    response = client.post(
        "/apartment",
        json={
            "country": "Australia",
            "country_code": "AU",
            "display_name": "1 Test St, Sydney, Australia",
        },
    )

    assert response.status_code == 422


def test_cors_preflight_allows_the_local_frontend_origin(client):
    response = client.options(
        "/apartment",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_preflight_rejects_an_unknown_origin(client):
    response = client.options(
        "/apartment",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


# What the frontend sends: the "address" part of a Nominatim search result, plus
# its display name.
PICKED_ADDRESS = {
    "house_number": "12",
    "road": "Smith Street",
    "suburb": "Newtown",
    "city": "Sydney",
    "state": "New South Wales",
    "postcode": "2042",
    "country": "Australia",
    "country_code": "au",
    "display_name": "12, Smith Street, Newtown, Sydney, 2042, Australia",
}


def test_picking_an_address_creates_its_apartment(client, db):
    response = client.post("/apartments/from-osm", json=PICKED_ADDRESS)

    assert response.status_code == 201
    apartment = db.query(Apartment).one()
    assert response.json()["uid"] == str(apartment.uid)
    assert apartment.street == "Smith Street"
    assert apartment.house_number == "12"
    assert apartment.city == "Sydney"
    assert apartment.postcode == "2042"
    assert apartment.country_code == "AU"


def test_picking_the_same_address_again_returns_the_same_apartment(client, db):
    first = client.post("/apartments/from-osm", json=PICKED_ADDRESS)
    second = client.post("/apartments/from-osm", json=PICKED_ADDRESS)

    assert second.json()["uid"] == first.json()["uid"]
    assert db.query(Apartment).count() == 1
