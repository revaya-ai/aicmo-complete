"""Placid client: on-brand template composite images behind one account.

Stdlib only (urllib + json + os). No third-party HTTP library. No network call
ever happens unless the credential is present in the environment.

Credentials:
    PLACID_API_TOKEN      the Placid REST API token
    PLACID_TEMPLATE_UUID  optional default template uuid to composite against

Auth is a bearer token: the header is `Authorization: Bearer <token>`. Base URL
is https://api.placid.app/api/rest/. The images endpoint expects a JSON body of
the shape {"template_uuid": "...", "layers": {...}}, where layers map the
template's named slots (hook, body, brand color) to their values. Placid returns
a job with a polling `status` and eventually an `image_url`, so `get_image`
polls one image job by id.

If `is_configured()` is False, every method raises `PlacidNotConfigured` before
touching the network. The Studio render layer catches that and falls back to its
deterministic offline render (PIL, then stdlib placeholder). This is how the
whole system stays offline by default and only goes live with a credential.
"""

import json
import os
import urllib.request

BASE_URL = "https://api.placid.app/api/rest/"

_TOKEN_ENV = "PLACID_API_TOKEN"
_TEMPLATE_ENV = "PLACID_TEMPLATE_UUID"


class PlacidNotConfigured(RuntimeError):
    """Raised when a method is called without the API token in the env.

    Callers should catch this and fall back to the offline render. It is never
    raised after a network call, only before one, so catching it guarantees no
    socket was opened.
    """


class PlacidClient:
    """Thin typed wrapper over the Placid REST API. Stdlib only."""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 30):
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

    def default_template_uuid(self):
        return os.environ.get(_TEMPLATE_ENV)

    # ---- transport -----------------------------------------------------------

    def _request(self, endpoint: str, payload: dict = None, method: str = "POST") -> dict:
        """Send one request to an endpoint and return the parsed JSON.

        Raises PlacidNotConfigured if the token is missing, before any network
        access.
        """
        if not self.is_configured():
            raise PlacidNotConfigured(
                f"{_TOKEN_ENV} must be set to call Placid. "
                f"Falling back to the offline render."
            )
        url = self.base_url + endpoint.lstrip("/")
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", self._auth_header())
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ---- images --------------------------------------------------------------

    def render_image(self, template_uuid, layers: dict) -> dict:
        """Start an image render job from a template and its layer values.

        POST images with body {"template_uuid": ..., "layers": {...}}. Placid
        returns a job with a `status` and, once finished, an `image_url`. If
        `template_uuid` is None, the PLACID_TEMPLATE_UUID env default is used.
        """
        uuid = template_uuid or self.default_template_uuid()
        return self._request(
            "images",
            {"template_uuid": uuid, "layers": layers or {}},
            method="POST",
        )

    def get_image(self, image_id: str) -> dict:
        """Poll one image job by id. Returns its current status (and image_url
        once finished)."""
        return self._request(f"images/{image_id}", method="GET")
