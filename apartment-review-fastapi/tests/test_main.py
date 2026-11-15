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
