"""Backblaze B2 client: off-site backup of pipeline artifacts behind one account.

Stdlib only (urllib + base64 + json + hashlib + os). No third-party HTTP
library. No network call ever happens unless all three credentials are present
in the environment.

Credentials:
    BACKBLAZE_KEY_ID           the B2 application key id
    BACKBLAZE_APPLICATION_KEY  the B2 application key secret
    BACKBLAZE_BUCKET           the target bucket name

The B2 native API uploads in three steps. First the authorize handshake: GET
b2_authorize_account with HTTP Basic auth built from the key id and application
key, which returns an authorizationToken and an apiUrl. Second, b2_get_upload_url
returns a one-shot uploadUrl and upload token. Third, the file bytes are POSTed
to that uploadUrl with the upload token, the remote file name, the content sha1,
and the content length.

If is_configured() is False, every method raises BackblazeNotConfigured before
touching the network. The backup helper catches that and falls back to a local
offline manifest, so the whole system stays offline by default and only ships
bytes off-site once a credential is present. No money spent, no socket opened, in
tests or CI.
"""

import base64
import hashlib
import json
import os
import urllib.request

AUTHORIZE_URL = "https://api.backblazeb2.com/b2api/v3/b2_authorize_account"

_KEY_ID_ENV = "BACKBLAZE_KEY_ID"
_APP_KEY_ENV = "BACKBLAZE_APPLICATION_KEY"
_BUCKET_ENV = "BACKBLAZE_BUCKET"


class BackblazeNotConfigured(RuntimeError):
    """Raised when a method is called without all three credentials in the env.

    Callers should catch this and fall back to the local offline manifest. It is
    never raised after a network call, only before one, so catching it guarantees
    no bytes left the machine and no socket was opened.
    """


class BackblazeClient:
    """Thin typed wrapper over the Backblaze B2 native API. Stdlib only."""

    def __init__(self, authorize_url: str = AUTHORIZE_URL, timeout: int = 60):
        self.authorize_url = authorize_url
        self.timeout = timeout

    # ---- configuration -------------------------------------------------------

    def _credentials(self):
        return (
            os.environ.get(_KEY_ID_ENV),
            os.environ.get(_APP_KEY_ENV),
            os.environ.get(_BUCKET_ENV),
        )

    def is_configured(self) -> bool:
        """True only when all three env vars are set and non-empty."""
        key_id, app_key, bucket = self._credentials()
        return bool(key_id) and bool(app_key) and bool(bucket)

    def _basic_auth_header(self) -> str:
        key_id, app_key, _bucket = self._credentials()
        raw = f"{key_id}:{app_key}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("ascii")

    # ---- transport -----------------------------------------------------------

    def _get_json(self, url: str, auth_header: str) -> dict:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", auth_header)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ---- handshake -----------------------------------------------------------

    def authorize(self) -> dict:
        """Authorize handshake. Returns the parsed JSON with apiUrl and a token.

        Raises BackblazeNotConfigured if credentials are missing, before any
        network access.
        """
        if not self.is_configured():
            raise BackblazeNotConfigured(
                f"{_KEY_ID_ENV}, {_APP_KEY_ENV}, and {_BUCKET_ENV} must all be "
                f"set to call Backblaze. Falling back to the offline manifest."
            )
        return self._get_json(self.authorize_url, self._basic_auth_header())

    # ---- upload --------------------------------------------------------------

    def backup_file(self, local_path: str, remote_name: str) -> dict:
        """Upload one local file to the bucket under remote_name.

        Three step B2 native upload: authorize, get an upload url, then POST the
        bytes. Returns the parsed upload result JSON. Raises
        BackblazeNotConfigured before any network access when unconfigured.
        """
        if not self.is_configured():
            raise BackblazeNotConfigured(
                f"{_KEY_ID_ENV}, {_APP_KEY_ENV}, and {_BUCKET_ENV} must all be "
                f"set to call Backblaze. Falling back to the offline manifest."
            )

        auth = self.authorize()
        api_url = auth["apiUrl"].rstrip("/")
        account_token = auth["authorizationToken"]

        upload_creds = self._get_json(
            f"{api_url}/b2api/v3/b2_get_upload_url", account_token
        )
        upload_url = upload_creds["uploadUrl"]
        upload_token = upload_creds["authorizationToken"]

        with open(local_path, "rb") as fh:
            data = fh.read()
        sha1 = hashlib.sha1(data).hexdigest()

        req = urllib.request.Request(upload_url, data=data, method="POST")
        req.add_header("Authorization", upload_token)
        req.add_header("X-Bz-File-Name", urllib.request.quote(remote_name))
        req.add_header("Content-Type", "b2/x-auto")
        req.add_header("X-Bz-Content-Sha1", sha1)
        req.add_header("Content-Length", str(len(data)))
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
