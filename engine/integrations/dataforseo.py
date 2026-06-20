"""DataForSEO client: SEO and AEO signals behind one account.

Stdlib only (urllib + base64 + json). No third-party HTTP library. No network
call ever happens unless both credentials are present in the environment.

Credentials:
    DATAFORSEO_LOGIN     the account login (an email)
    DATAFORSEO_PASSWORD  the account password

Auth is HTTP Basic: the header is `Authorization: Basic <base64(login:password)>`.
Base URL is https://api.dataforseo.com/v3/. DataForSEO expects the request body
to be a JSON array of task objects, e.g. [{"keyword": "..."}], so `_post` always
wraps the single task in a list.

If `is_configured()` is False, every method raises `DataForSEONotConfigured`
before touching the network. Callers (the Intelligence layer, the AEO module)
catch that and fall back to their deterministic offline stub. This is how the
whole system stays offline by default and only goes live with credentials.

Cost note: DataForSEO is pay-as-you-go with a $50 minimum deposit. Calls are
cheap (fractions of a cent each) but they are real money, so the gate matters.
"""

import base64
import json
import os
import urllib.request

BASE_URL = "https://api.dataforseo.com/v3/"

_LOGIN_ENV = "DATAFORSEO_LOGIN"
_PASSWORD_ENV = "DATAFORSEO_PASSWORD"


class DataForSEONotConfigured(RuntimeError):
    """Raised when a method is called without both credentials in the env.

    Callers should catch this and fall back to the offline stub. It is never
    raised after a network call, only before one, so catching it guarantees no
    money was spent and no socket was opened.
    """


class DataForSEOClient:
    """Thin typed wrapper over the DataForSEO v3 API. Stdlib only."""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    # ---- configuration -------------------------------------------------------

    def _credentials(self):
        return os.environ.get(_LOGIN_ENV), os.environ.get(_PASSWORD_ENV)

    def is_configured(self) -> bool:
        """True only when both env vars are set and non-empty."""
        login, password = self._credentials()
        return bool(login) and bool(password)

    def _auth_header(self) -> str:
        login, password = self._credentials()
        raw = f"{login}:{password}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("ascii")

    # ---- transport -----------------------------------------------------------

    def _post(self, endpoint: str, payload: dict) -> dict:
        """POST one task object to an endpoint and return the parsed JSON.

        Raises DataForSEONotConfigured if credentials are missing, before any
        network access. The body is sent as a JSON ARRAY of task objects, per the
        DataForSEO convention.
        """
        if not self.is_configured():
            raise DataForSEONotConfigured(
                f"{_LOGIN_ENV} and {_PASSWORD_ENV} must both be set to call "
                f"DataForSEO. Falling back to the offline stub."
            )
        url = self.base_url + endpoint.lstrip("/")
        body = json.dumps([payload]).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", self._auth_header())
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ---- SEO -----------------------------------------------------------------

    def serp_organic_live(
        self,
        keyword: str,
        location_name: str = "United States",
        language_code: str = "en",
    ) -> dict:
        """Real-time Google organic SERP for one keyword."""
        return self._post(
            "serp/google/organic/live/advanced",
            {
                "keyword": keyword,
                "location_name": location_name,
                "language_code": language_code,
            },
        )

    def keyword_ideas(
        self,
        keywords: list,
        location_name: str = "United States",
        language_code: str = "en",
    ) -> dict:
        """Keyword ideas related to the seed keywords (DataForSEO Labs)."""
        return self._post(
            "dataforseo_labs/google/keyword_ideas/live",
            {
                "keywords": list(keywords),
                "location_name": location_name,
                "language_code": language_code,
            },
        )

    def related_keywords(
        self,
        keyword: str,
        location_name: str = "United States",
        language_code: str = "en",
    ) -> dict:
        """Related keywords for one seed keyword (DataForSEO Labs)."""
        return self._post(
            "dataforseo_labs/google/related_keywords/live",
            {
                "keyword": keyword,
                "location_name": location_name,
                "language_code": language_code,
            },
        )

    def search_volume(
        self,
        keywords: list,
        location_name: str = "United States",
        language_code: str = "en",
    ) -> dict:
        """Real Google Ads search volume for a list of keywords."""
        return self._post(
            "keywords_data/google_ads/search_volume/live",
            {
                "keywords": list(keywords),
                "location_name": location_name,
                "language_code": language_code,
            },
        )

    # ---- AEO -----------------------------------------------------------------

    def ai_keyword_data(
        self,
        keywords: list,
        location_name: str = "United States",
        language_code: str = "en",
    ) -> dict:
        """AI search volume: how people phrase queries inside AI tools."""
        return self._post(
            "ai_optimization/ai_keyword_data/keywords_search_volume/live",
            {
                "keywords": list(keywords),
                "location_name": location_name,
                "language_code": language_code,
            },
        )

    def llm_responses(self, prompt: str, model: str = "chat_gpt") -> dict:
        """Ask one target question across an LLM and see what it answers.

        `model` is the DataForSEO model slug (e.g. chat_gpt, gemini). It is
        substituted into the endpoint path.
        """
        return self._post(
            f"ai_optimization/{model}/llm_responses/live",
            {"user_prompt": prompt},
        )

    def llm_mentions(
        self,
        target: str,
        model: str = "chat_gpt",
        location_name: str = "United States",
    ) -> dict:
        """Whether the brand/target is mentioned or cited in LLM answers."""
        return self._post(
            f"ai_optimization/{model}/llm_responses/live",
            {"user_prompt": target, "location_name": location_name},
        )
