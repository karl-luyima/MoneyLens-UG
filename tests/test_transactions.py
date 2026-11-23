"""Tests for MoneyLens UG transaction endpoints."""


def create_transaction(client, auth_headers, transaction_id, amount=35000):
    """Create a synthetic transaction through the upload endpoint."""

    message = (
        f"You have sent UGX {amount:,} to 0772000111 (John Doe). "
        f"Transaction ID: {transaction_id}. Fee: UGX 700. "
        f"New balance: UGX 90,000. Date: 23/11/2026 12:00."
    )

    return client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={"messages": [message]},
    )


def test_get_transactions(client, auth_headers):
    """Authenticated users should retrieve their transactions."""

    create_transaction(client, auth_headers, "TRANSACTION001")

    response = client.get(
        "/api/v1/transactions",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_filter_transactions_by_provider(client, auth_headers):
    """Transactions should be filterable by provider."""

    create_transaction(client, auth_headers, "PROVIDER001")

    response = client.get(
        "/api/v1/transactions?provider=MTN",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) >= 1

    for transaction in data["items"]:
        assert transaction["provider"] == "MTN"


def test_filter_transactions_by_type(client, auth_headers):
    """Transactions should be filterable by transaction type."""

    create_transaction(client, auth_headers, "TYPE001")

    response = client.get(
        "/api/v1/transactions?transaction_type=send_money",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) >= 1

    for transaction in data["items"]:
        assert transaction["transaction_type"] == "send_money"


def test_filter_transactions_by_amount(client, auth_headers):
    """Transactions should be filterable by amount range."""

    create_transaction(
        client,
        auth_headers,
        "AMOUNT001",
        amount=35000,
    )

    response = client.get(
        "/api/v1/transactions?min_amount=30000&max_amount=40000",
        headers=auth_headers,
    )

    assert response.status_code == 200

    for transaction in response.json()["items"]:
        assert 30000 <= float(transaction["amount"]) <= 40000


def test_transaction_pagination(client, auth_headers):
    """Transaction results should support pagination."""

    create_transaction(client, auth_headers, "PAGE001")
    create_transaction(client, auth_headers, "PAGE002")
    create_transaction(client, auth_headers, "PAGE003")

    response = client.get(
        "/api/v1/transactions?page=1&page_size=2",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) <= 2


def test_invalid_provider(client, auth_headers):
    """Invalid providers should be rejected."""

    response = client.get(
        "/api/v1/transactions?provider=INVALID",
        headers=auth_headers,
    )

    assert response.status_code == 400


def test_invalid_date_range(client, auth_headers):
    """Invalid date ranges should be rejected."""

    response = client.get(
        "/api/v1/transactions"
        "?date_from=2026-11-24T00:00:00"
        "&date_to=2026-11-23T00:00:00",
        headers=auth_headers,
    )

    assert response.status_code == 400


def test_invalid_amount_range(client, auth_headers):
    """Invalid amount ranges should be rejected."""

    response = client.get(
        "/api/v1/transactions?min_amount=50000&max_amount=10000",
        headers=auth_headers,
    )

    assert response.status_code == 400


def test_transactions_without_authentication(client):
    """Unauthenticated users should not retrieve transactions."""

    response = client.get("/api/v1/transactions")

    assert response.status_code == 401


def test_users_cannot_access_each_others_transactions(
    client,
    auth_headers,
):
    """Users should only see their own transactions."""

    # Create a transaction for the first authenticated user.
    first_upload = create_transaction(
        client,
        auth_headers,
        "USERONE001",
    )

    assert first_upload.status_code == 201

    # Register a second synthetic user.
    second_user_data = {
        "email": "seconduser@moneylens.ug",
        "password": "SecurePassword123!",
    }

    register_response = client.post(
        "/api/v1/auth/register",
        json=second_user_data,
    )

    assert register_response.status_code == 201

    # Log in as the second user.
    login_response = client.post(
        "/api/v1/auth/login",
        json=second_user_data,
    )

    assert login_response.status_code == 200

    second_access_token = login_response.json()["access_token"]

    second_auth_headers = {"Authorization": f"Bearer {second_access_token}"}

    # Create a transaction belonging to the second user.
    second_upload = create_transaction(
        client,
        second_auth_headers,
        "USERTWO001",
    )

    assert second_upload.status_code == 201

    # Retrieve transactions as the first user.
    first_user_response = client.get(
        "/api/v1/transactions",
        headers=auth_headers,
    )

    assert first_user_response.status_code == 200

    first_user_transactions = first_user_response.json()["items"]

    first_user_transaction_ids = [
        transaction["transaction_id"] for transaction in first_user_transactions
    ]

    assert "USERONE001" in first_user_transaction_ids
    assert "USERTWO001" not in first_user_transaction_ids

    # Retrieve transactions as the second user.
    second_user_response = client.get(
        "/api/v1/transactions",
        headers=second_auth_headers,
    )

    assert second_user_response.status_code == 200

    second_user_transactions = second_user_response.json()["items"]

    second_user_transaction_ids = [
        transaction["transaction_id"] for transaction in second_user_transactions
    ]

    assert "USERTWO001" in second_user_transaction_ids
    assert "USERONE001" not in second_user_transaction_ids
