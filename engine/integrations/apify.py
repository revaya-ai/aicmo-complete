"""Apify client: competitor and web scrape signals behind one token.

Stdlib only (urllib + json + os). No third-party HTTP library. No network call
ever happens unless the token is present in the environment.

Credentials:
    APIFY_TOKEN  the Apify API token

Auth is a bearer token sent in the header, never in the URL query string:
`Authorization: Bearer <token>`. Base URL is https://api.apify.com/v2/. This
client uses the run-sync-get-dataset-items endpoint, which runs an actor and
returns its dataset items in one synchronous call:
acts/{actor_id}/run-sync-get-dataset-items. Apify returns a JSON array of
dataset items, so run_actor_get_items returns a list (and tolerates an empty or
odd shape by returning []).

If `is_configured()` is False, every method raises `ApifyNotConfigured` before
touching the network. The Intelligence layer catches that and falls back to its
deterministic offline stub. This is how the whole system stays offline by default
and only goes live with a credential.

Cost note: Apify is paid compute. Every actor run consumes compute units that
cost real money, and run-sync holds a connection open for the whole run. The gate
matters: never call without the token set, and never log the token.
"""

import json
import os
import urllib.request

BASE_URL = "https://api.apify.com/v2/"

_TOKEN_ENV = "APIFY_TOKEN"


class ApifyNotConfigured(RuntimeError):
    """Raised when a method is called without the API token in the env.

    Callers should catch this and fall back to the offline stub. It is never
    raised after a network call, only before one, so catching it guarantees no
    compute units were spent and no socket was opened.
    """


class ApifyClient:
    """Thin typed wrapper over the Apify v2 API. Stdlib only."""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 120):
        self.base_url = base_url
        self.timeout = timeout

    # ---- configuration -------------------------------------------------------

    def _token(self):
        return os.environ.get(_TOKEN_ENV)

    def is_configured(self) -> bool:
        """True only when the API token is set and non-empty."""
        return bool(self._token())

    def _auth_header(self) -> str:
        return "Bearer " + (self._token() or "")

    # ---- transport -----------------------------------------------------------

    def _post(self, endpoint: str, payload: dict):
        """POST a JSON body to an endpoint and return the parsed JSON.

        Raises ApifyNotConfigured if the token is missing, before any network
        access. The token rides in the Authorization header, never in the URL.
        """
        if not self.is_configured():
            raise ApifyNotConfigured(
                f"{_TOKEN_ENV} must be set to call Apify. "
                f"Falling back to the offline stub."
            )
        url = self.base_url + endpoint.lstrip("/")
        body = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", self._auth_header())
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ---- actors --------------------------------------------------------------

    def run_actor_get_items(self, actor_id: str, run_input: dict) -> list:
        """Run an actor synchronously and return its dataset items as a list.

        POSTs run_input to acts/{actor_id}/run-sync-get-dataset-items. Apify
        returns a JSON array of dataset items. If the response is not a list
        (empty body, error object, or odd shape) this returns [] so a thin
        response degrades to the offline stub rather than crashing the caller.
        """
        result = self._post(
            f"acts/{actor_id}/run-sync-get-dataset-items",
            run_input,
        )
        if isinstance(result, list):
            return result
        return []
