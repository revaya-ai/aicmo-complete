"""Google Search Console client: real Search demand behind one property.

Stdlib only (urllib + json + os). No third-party HTTP library. No network call
ever happens unless both credentials are present in the environment.

Auth note: Google's Search Console API normally uses an OAuth2 service-account
flow that needs the google-auth library. To stay stdlib-only and credential-gated
like every other integration here, this client does NOT implement the OAuth
handshake. It consumes a PRE-OBTAINED OAuth2 bearer access token supplied through
the environment. The token is obtained externally (by an operator or a separate
refresh step); this client only spends it. That keeps the dependency surface at
the standard library and matches the repo's offline-by-default contract.

Credentials:
    GSC_ACCESS_TOKEN  a pre-obtained OAuth2 bearer access token
    GSC_SITE_URL      the verified property, e.g. https://lumenskin.com/

Auth is a bearer token: the header is `Authorization: Bearer <token>`. The
Search Analytics endpoint is
https://www.googleapis.com/webmasters/v3/sites/{siteUrl}/searchAnalytics/query
where {siteUrl} is the URL-encoded property. The body is a JSON object with
startDate, endDate, dimensions, and rowLimit. Google returns {"rows": [...]} so
search_analytics returns the parsed JSON for the caller to read.

If `is_configured()` is False, every method raises `GSCNotConfigured` before
touching the network. The Intelligence layer catches that and falls back to its
deterministic offline stub. This is how the whole system stays offline by default
and only goes live with credentials.

Cost note: the Search Console API is free, but it is rate limited per property
and the access token is a real, scoped credential. The gate still matters: never
call without both env vars set, and never log the token.
"""

import json
import os
import urllib.parse
import urllib.request

BASE_URL = "https://www.googleapis.com/webmasters/v3/"

_TOKEN_ENV = "GSC_ACCESS_TOKEN"
_SITE_ENV = "GSC_SITE_URL"


class GSCNotConfigured(RuntimeError):
    """Raised when a method is called without both credentials in the env.

    Callers should catch this and fall back to the offline stub. It is never
    raised after a network call, only before one, so catching it guarantees no
    socket was opened.
    """


class GSCClient:
    """Thin typed wrapper over the Search Console v3 API. Stdlib only."""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    # ---- configuration -------------------------------------------------------

    def _token(self):
        return os.environ.get(_TOKEN_ENV)

    def _site_url(self):
        return os.environ.get(_SITE_ENV)

    def is_configured(self) -> bool:
        """True only when both the access token and the site url are non-empty."""
        return bool(self._token()) and bool(self._site_url())

    def _auth_header(self) -> str:
        return "Bearer " + (self._token() or "")

    # ---- transport -----------------------------------------------------------

    def _post(self, endpoint: str, payload: dict) -> dict:
        """POST a JSON body to an endpoint and return the parsed JSON.

        Raises GSCNotConfigured if either credential is missing, before any
        network access.
        """
        if not self.is_configured():
            raise GSCNotConfigured(
                f"{_TOKEN_ENV} and {_SITE_ENV} must both be set to call "
                f"Search Console. Falling back to the offline stub."
            )
        url = self.base_url + endpoint.lstrip("/")
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", self._auth_header())
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ---- search analytics ----------------------------------------------------

    def search_analytics(
        self,
        start_date: str,
        end_date: str,
        dimensions: list = None,
        row_limit: int = 25,
    ) -> dict:
        """Query Search Analytics for the configured property.

        POSTs to sites/{siteUrl}/searchAnalytics/query with the date range,
        dimensions (default ["query"]), and rowLimit. The siteUrl path segment is
        URL-encoded so a full property url like https://lumenskin.com/ is safe in
        the path. Returns the parsed JSON, typically {"rows": [...]}.
        """
        site = urllib.parse.quote(self._site_url() or "", safe="")
        return self._post(
            f"sites/{site}/searchAnalytics/query",
            {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": dimensions or ["query"],
                "rowLimit": row_limit,
            },
        )
