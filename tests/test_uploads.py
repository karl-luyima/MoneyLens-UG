
"""Tests for MoneyLens UG upload endpoints."""

from app.models.category import Category
from app.models.transaction import Transaction


def test_upload_valid_messages(client, auth_headers):
    """Valid messages should be parsed and saved."""

    response = client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={
            "messages": [
                "You have sent UGX 35,000 to 0772000111 (John Doe). "
                "Transaction ID: TESTUPLOAD001. Fee: UGX 700. "
                "New balance: UGX 90,000. Date: 23/11/2026 12:00."
            ]
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["total_messages"] == 1
    assert data["parsed_count"] == 1
    assert data["duplicate_count"] == 0
    assert data["unparsed_count"] == 0
    assert data["status"] == "completed"


def test_upload_faras_transaction_is_categorized_as_transport(
    client,
    auth_headers,
    db_session,
):
    """Uploaded FARAS transactions should be saved under Transport."""

    response = client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={
            "messages": [
                "You have sent UGX 35,000 to 0772000111 (FARAS). "
                "Transaction ID: TESTFARAS001. Fee: UGX 700. "
                "New balance: UGX 90,000. Date: 23/11/2026 14:00."
            ]
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["parsed_count"] == 1
    assert data["duplicate_count"] == 0
    assert data["unparsed_count"] == 0

    # Retrieve the saved transaction from the test database.
    transaction = db_session.query(Transaction).filter_by(
        transaction_id="TESTFARAS001",
    ).one()

    # Retrieve its assigned category.
    category = db_session.query(Category).filter_by(
        id=transaction.category_id,
    ).one()

    assert category.name == "Transport"


def test_upload_duplicate_across_uploads(client, auth_headers):
    """Previously imported transactions should be detected."""

    message = (
        "You have sent UGX 20,000 to 0772000111 (John Doe). "
        "Transaction ID: TESTDUPLICATE001. Fee: UGX 500. "
        "New balance: UGX 70,000. Date: 23/11/2026 12:10."
    )

    first_response = client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={"messages": [message]},
    )

    second_response = client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={"messages": [message]},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["parsed_count"] == 1
    assert second_data["parsed_count"] == 0
    assert second_data["duplicate_count"] == 1


def test_upload_duplicate_within_same_batch(client, auth_headers):
    """Repeated transaction IDs in one upload should be detected."""

    message = (
        "You have sent UGX 35,000 to 0772000111 (John Doe). "
        "Transaction ID: TESTBATCH001. Fee: UGX 700. "
        "New balance: UGX 90,000. Date: 23/11/2026 12:20."
    )

    response = client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={"messages": [message, message]},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["total_messages"] == 2
    assert data["parsed_count"] == 1
    assert data["duplicate_count"] == 1
    assert data["unparsed_count"] == 0


def test_upload_unrecognised_message(client, auth_headers):
    """Unrecognised messages should be saved as unparsed."""

    response = client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={"messages": ["This is an invalid synthetic transaction message."]},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["total_messages"] == 1
    assert data["parsed_count"] == 0
    assert data["duplicate_count"] == 0
    assert data["unparsed_count"] == 1


def test_upload_empty_messages(client, auth_headers):
    """An upload containing only blank messages should be rejected."""

    response = client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={"messages": ["", "   "]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "At least one non-empty message is required."
    )


def test_upload_without_authentication(client):
    """Unauthenticated users should not upload messages."""

    response = client.post(
        "/api/v1/uploads/messages",
        json={"messages": ["Synthetic message"]},
    )

    assert response.status_code == 401


def test_upload_txt_file(client, auth_headers):
    """A valid TXT file should be processed successfully."""

    content = (
        "You have sent UGX 25,000 to 0772000111 (John Doe). "
        "Transaction ID: TESTTXT001. Fee: UGX 500. "
        "New balance: UGX 90,000. Date: 23/11/2026 12:30.\n"
    )

    response = client.post(
        "/api/v1/uploads/file",
        headers=auth_headers,
        files={
            "file": (
                "synthetic.txt",
                content.encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["parsed_count"] == 1
    assert response.json()["source_type"] == "file"


def test_upload_csv_file(client, auth_headers):
    """A valid CSV file should be processed successfully."""

    content = (
        "message\n"
        '"You have sent UGX 30,000 to 0772000111 (John Doe). '
        "Transaction ID: TESTCSV001. Fee: UGX 600. "
        'New balance: UGX 90,000. Date: 23/11/2026 12:35."\n'
    )

    response = client.post(
        "/api/v1/uploads/file",
        headers=auth_headers,
        files={
            "file": (
                "synthetic.csv",
                content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["parsed_count"] == 1
    assert response.json()["source_type"] == "file"


def test_upload_unsupported_file(client, auth_headers):
    """Unsupported file extensions should be rejected."""

    response = client.post(
        "/api/v1/uploads/file",
        headers=auth_headers,
        files={
            "file": (
                "synthetic.pdf",
                b"Synthetic file content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400


def test_upload_empty_file(client, auth_headers):
    """An empty file should be rejected."""

    response = client.post(
        "/api/v1/uploads/file",
        headers=auth_headers,
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400


def test_get_upload_history(client, auth_headers):
    """Authenticated users should retrieve their upload history."""

    upload_response = client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={
            "messages": [
                "You have sent UGX 15,000 to 0772000111 (John Doe). "
                "Transaction ID: HISTORY001. Fee: UGX 300. "
                "New balance: UGX 90,000. Date: 23/11/2026 13:00."
            ]
        },
    )

    assert upload_response.status_code == 201

    response = client.get(
        "/api/v1/uploads",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_upload_history_pagination(client, auth_headers):
    """Upload history should support pagination."""

    for index in range(3):
        response = client.post(
            "/api/v1/uploads/messages",
            headers=auth_headers,
            json={"messages": [f"Invalid synthetic message {index}"]},
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/uploads?page=1&page_size=2",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2


def test_users_cannot_access_each_others_upload_history(
    client,
    auth_headers,
):
    """Users should only see their own upload records."""

    # Create an upload for the first user.
    first_upload = client.post(
        "/api/v1/uploads/messages",
        headers=auth_headers,
        json={"messages": ["Invalid synthetic message belonging to user one."]},
    )

    assert first_upload.status_code == 201

    # Register a second synthetic user.
    second_user_data = {
        "email": "uploaduser2@moneylens.ug",
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

    # Create an upload for the second user.
    second_upload = client.post(
        "/api/v1/uploads/messages",
        headers=second_auth_headers,
        json={"messages": ["Invalid synthetic message belonging to user two."]},
    )

    assert second_upload.status_code == 201

    # Retrieve upload history as the first user.
    first_history = client.get(
        "/api/v1/uploads",
        headers=auth_headers,
    )

    assert first_history.status_code == 200

    first_data = first_history.json()

    assert first_data["total"] == 1
    assert len(first_data["items"]) == 1

    # Retrieve upload history as the second user.
    second_history = client.get(
        "/api/v1/uploads",
        headers=second_auth_headers,
    )

    assert second_history.status_code == 200

    second_data = second_history.json()

    assert second_data["total"] == 1
    assert len(second_data["items"]) == 1

    # Confirm that the two users have different upload records.
    assert first_data["items"][0]["id"] != second_data["items"][0]["id"]
