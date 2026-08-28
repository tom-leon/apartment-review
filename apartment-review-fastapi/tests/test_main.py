def test_create_user_returns_response_without_password(client):
    response = client.post(
        "/user",
        json={"name": "Tom", "email": "tom@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Tom"
    assert body["email"] == "tom@example.com"
    assert "password" not in body


def test_create_user_rejects_missing_email(client):
    response = client.post("/user", json={"name": "Tom", "password": "secret123"})

    assert response.status_code == 422


def test_create_apartment_returns_response(client):
    response = client.post(
        "/apartment",
        json={
            "city": "Sydney",
            "country": "Australia",
            "country_code": "AU",
            "display_name": "1 Test St, Sydney, Australia",
            "latitude": "-33.8688",
            "longitude": "151.2093",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Sydney"
    assert "uid" in body


def test_create_apartment_rejects_missing_city(client):
    response = client.post(
        "/apartment",
        json={
            "country": "Australia",
            "country_code": "AU",
            "display_name": "1 Test St, Sydney, Australia",
            "latitude": "-33.8688",
            "longitude": "151.2093",
        },
    )

    assert response.status_code == 422
