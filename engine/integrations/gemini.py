"""Gemini image client (Nano Banana): on-brand generated images behind one key.

Stdlib only (urllib + base64 + json + os). No third-party HTTP library. No
network call ever happens unless the credential is present in the environment.

Credentials:
    GEMINI_API_KEY  the Google Generative Language API key

Auth is a header, not a query string: the request carries `x-goog-api-key:
<key>`. Keeping the key out of the URL keeps it out of logs and proxies. Base
URL is https://generativelanguage.googleapis.com/v1beta/. The image model is
gemini-2.5-flash-image (Nano Banana), called via the generateContent endpoint.
The request body is {"contents": [{"parts": [{"text": prompt}]}]}, and the image
comes back as base64 inside candidates[0].content.parts[*].inlineData.data, so
generate_image scans the parts for the first inline image and returns its raw
bytes.

If `is_configured()` is False, generate_image raises `GeminiNotConfigured`
before touching the network. The Studio render layer catches that and falls back
to its deterministic offline render (PIL, then stdlib placeholder). This is how
the whole system stays offline by default and only goes live with a credential.

Cost note: Gemini image generation is real, billed usage. Calls cost actual
money, so the credential gate matters: no key, no call.
"""

import base64
import json
import os
import urllib.request

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/"
MODEL = "gemini-2.5-flash-image"

_KEY_ENV = "GEMINI_API_KEY"


class GeminiNotConfigured(RuntimeError):
    """Raised when generate_image is called without the API key in the env.

    Callers should catch this and fall back to the offline render. It is never
    raised after a network call, only before one, so catching it guarantees no
    money was spent and no socket was opened.
    """


class GeminiImageClient:
    """Thin typed wrapper over the Gemini image generation API. Stdlib only."""

    def __init__(self, base_url: str = BASE_URL, model: str = MODEL, timeout: int = 60):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    # ---- configuration -------------------------------------------------------

    def _key(self):
        return os.environ.get(_KEY_ENV)

    def is_configured(self) -> bool:
        """True only when the API key is set and non-empty."""
        return bool(self._key())

    # ---- transport -----------------------------------------------------------

    def _post(self, endpoint: str, payload: dict) -> dict:
        """POST a JSON body to an endpoint and return the parsed JSON.

        Raises GeminiNotConfigured if the key is missing, before any network
        access. The key is sent as the x-goog-api-key header, never in the URL.
        """
        if not self.is_configured():
            raise GeminiNotConfigured(
                f"{_KEY_ENV} must be set to call Gemini. "
                f"Falling back to the offline render."
            )
        url = self.base_url + endpoint.lstrip("/")
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("x-goog-api-key", self._key())
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ---- images --------------------------------------------------------------

    def generate_image(self, prompt: str) -> bytes:
        """Generate one image from a text prompt and return its raw bytes.

        POST models/<model>:generateContent with a single text part. The
        response returns the image as base64 in
        candidates[0].content.parts[*].inlineData.data. The first part that
        carries inline image data is decoded and returned. If no inline image is
        present, a RuntimeError is raised so the render caller falls back offline.
        """
        result = self._post(
            f"models/{self.model}:generateContent",
            {"contents": [{"parts": [{"text": prompt}]}]},
        )
        data = self._extract_inline_image(result)
        if data is None:
            raise RuntimeError(
                "Gemini response carried no inline image data. "
                "Falling back to the offline render."
            )
        return base64.b64decode(data)

    @staticmethod
    def _extract_inline_image(result: dict):
        """Return the first inlineData.data string in the response, or None.

        Tolerates both camelCase (inlineData) and snake_case (inline_data) part
        keys, since the API has used both shapes.
        """
        for candidate in (result or {}).get("candidates", []) or []:
            parts = ((candidate or {}).get("content", {}) or {}).get("parts", []) or []
            for part in parts:
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    return inline["data"]
        return None
