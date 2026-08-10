import time
from typing import Optional

import requests


class PaloAltoSCMClient:
    """
    Authenticated HTTP client for Palo Alto Strata Cloud Manager (SCM).

    Handles OAuth2 client_credentials token generation and refresh internally.
    Callers only need to supply the API path/method (and optional body/params).
    """

    def __init__(
        self,
        protocol: str,
        host: str,
        auth_url: str,
        client_id: str,
        client_secret: str,
        scope: str,
    ) -> None:
        self.base_url = f"{protocol.rstrip(':/')}://{host.strip('/')}"
        self.auth_url = auth_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.session = requests.Session()
        self._access_token: Optional[str] = None
        self._expires_at: float = 0

    def _get_access_token(self) -> str:
        # Reuse cached token with a 60-second safety buffer
        if self._access_token and time.time() < self._expires_at - 60:
            return self._access_token

        response = self.session.post(
            self.auth_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.scope,
            },
            timeout=30,
        )
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Token response did not contain an access_token")

        self._access_token = access_token
        self._expires_at = time.time() + float(token_data.get("expires_in", 300))
        return self._access_token

    def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> requests.Response:
        """
        Perform an authenticated request against the SCM API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, ...).
            endpoint: API path relative to the base URL, e.g. /config/setup/v1/devices.
            headers: Optional extra headers (Authorization is set automatically).
            **kwargs: Passed through to requests.Session.request (params, json, data, timeout, ...).
        """
        token = self._get_access_token()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        combined_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        if headers:
            for key, value in headers.items():
                if key.lower() != "authorization":
                    combined_headers[key] = value

        if "timeout" not in kwargs:
            kwargs["timeout"] = 30

        return self.session.request(method, url, headers=combined_headers, **kwargs)
