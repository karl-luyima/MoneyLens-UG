
"""HTTP client for communicating with the MoneyLens UG API."""

import os
from datetime import date
from typing import Any, cast

import httpx

API_BASE_URL = os.getenv(
    "MONEYLENS_API_URL",
    "http://127.0.0.1:8000/api/v1",
)


class APIError(Exception):
    """Raised when an API request fails."""


class APIClient:
    """Handles authenticated and unauthenticated API requests."""

    def __init__(self, access_token: str | None = None) -> None:
        self.base_url = API_BASE_URL.rstrip("/")
        self.access_token = access_token

    def _headers(self) -> dict[str, str]:
        """Build request headers."""

        headers = {"Accept": "application/json"}

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        """Send an HTTP request and handle API errors."""

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = httpx.request(
                method,
                url,
                headers=self._headers(),
                timeout=30.0,
                **kwargs,
            )
            response.raise_for_status()

            if response.status_code == 204:
                return None

            return response.json()

        except httpx.HTTPStatusError as exc:
            try:
                detail = exc.response.json().get(
                    "detail",
                    exc.response.text,
                )
            except ValueError:
                detail = exc.response.text

            raise APIError(
                f"API error ({exc.response.status_code}): {detail}"
            ) from exc

        except httpx.RequestError as exc:
            raise APIError(
                "Could not connect to MoneyLens UG API. "
                "Ensure the FastAPI server is running."
            ) from exc

    def register(self, email: str, password: str) -> dict[str, Any]:
        """Register a new user."""

        return cast(
            dict[str, Any],
            self._request(
                "POST",
                "/auth/register",
                json={"email": email, "password": password},
            ),
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate a user and return JWT tokens."""

        return cast(
            dict[str, Any],
            self._request(
                "POST",
                "/auth/login",
                json={"email": email, "password": password},
            ),
        )

    def refresh_token(
        self,
        refresh_token: str,
    ) -> dict[str, Any]:
        """Obtain a new access token."""

        return cast(
            dict[str, Any],
            self._request(
                "POST",
                "/auth/refresh",
                json={"refresh_token": refresh_token},
            ),
        )

    def upload_messages(
        self,
        messages: list[str],
    ) -> dict[str, Any]:
        """Upload pasted mobile money messages."""

        return cast(
            dict[str, Any],
            self._request(
                "POST",
                "/uploads/messages",
                json={"messages": messages},
            ),
        )

    def upload_file(
        self,
        file_name: str,
        file_bytes: bytes,
    ) -> dict[str, Any]:
        """Upload a TXT or CSV file."""

        return cast(
            dict[str, Any],
            self._request(
                "POST",
                "/uploads/file",
                files={
                    "file": (
                        file_name,
                        file_bytes,
                        "application/octet-stream",
                    )
                },
            ),
        )

    def get_uploads(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Retrieve paginated upload history."""

        return cast(
            dict[str, Any],
            self._request(
                "GET",
                "/uploads",
                params={
                    "page": page,
                    "page_size": page_size,
                },
            ),
        )

    def get_transactions(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters: Any,
    ) -> dict[str, Any]:
        """Retrieve transactions with optional filters."""

        params = {
            "page": page,
            "page_size": page_size,
        }

        params.update(
            {
                key: value
                for key, value in filters.items()
                if value is not None and value != ""
            }
        )

        return cast(
            dict[str, Any],
            self._request(
                "GET",
                "/transactions",
                params=params,
            ),
        )

    def update_transaction_category(
        self,
        transaction_id: int,
        category_id: int,
    ) -> dict[str, Any]:
        """Correct a transaction's category."""

        return cast(
            dict[str, Any],
            self._request(
                "PATCH",
                f"/transactions/{transaction_id}/category",
                json={"category_id": category_id},
            ),
        )

    def get_categories(self) -> list[dict[str, Any]]:
        """Retrieve system and user-defined categories."""

        return cast(
            list[dict[str, Any]],
            self._request("GET", "/categories/"),
        )

    def get_insights(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Retrieve financial insights for an optional date range."""

        params = {}

        if start_date is not None:
            params["start_date"] = start_date.isoformat()

        if end_date is not None:
            params["end_date"] = end_date.isoformat()

        return cast(
            dict[str, Any],
            self._request(
                "GET",
                "/insights/summary",
                params=params,
            ),
        )

    def retrain_category_model(self) -> dict[str, Any]:
        """Retrain the personalized categorization model."""

        return cast(
            dict[str, Any],
            self._request("POST", "/categories/retrain"),
        )
