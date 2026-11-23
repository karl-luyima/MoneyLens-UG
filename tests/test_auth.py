"""Tests for MoneyLens UG authentication endpoints."""


def test_register_user(client):
    """A new user should be registered successfully."""

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@moneylens.ug",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "newuser@moneylens.ug"


def test_register_duplicate_email(client):
    """Registering an existing email should return 409."""

    user_data = {
        "email": "duplicate@moneylens.ug",
        "password": "SecurePassword123!",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_user(client):
    """A registered user should receive authentication tokens."""

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginuser@moneylens.ug",
            "password": "SecurePassword123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "loginuser@moneylens.ug",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_login_invalid_password(client):
    """An incorrect password should return 401."""

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpassword@moneylens.ug",
            "password": "SecurePassword123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpassword@moneylens.ug",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_get_current_user_profile(client, auth_headers):
    """An authenticated user should retrieve their profile."""

    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["email"] == "pytest_user@moneylens.ug"


def test_get_profile_without_authentication(client):
    """An unauthenticated request should return 401."""

    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
