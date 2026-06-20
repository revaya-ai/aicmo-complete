# QA Report: DataForSEO Integration

**Auditor:** Independent QA (did not build this)
**Date:** 2026-06-20
**Scope:** `engine/integrations/dataforseo.py`, `engine/aeo/aeo.py`, `engine/intelligence/intelligence.py`, tests, `.claude/commands/ai-cmo-aeo.md`, `.env.example`, `README.md`, against `docs/integrations/dataforseo-brief.md`.
**Principle audited:** Watch for silence, not just errors. A "success" that produces nothing, or a credential gate that leaks a network call, is a failure even if no exception is raised.

---

## Top-line verdict: PASS

All 8 checks pass. The integration is offline by default, the credential gate is real with no bypass path, the live path only activates with injected/configured credentials, tests make no real network call (78 passed), no secrets are committed, generated output has zero em dashes, and the AEO report writes a real non-empty file. One minor brief-fidelity gap (3 endpoints named in the brief are not implemented) and one cosmetic test nit, neither blocking.

---

## 1. Credential gating is real (no silent network) — PASS

`engine/integrations/dataforseo.py` has exactly ONE place that touches the network: `_post()` line 85 (`urllib.request.urlopen`). `_post()` opens with a hard guard (lines 75-79):

```python
if not self.is_configured():
    raise DataForSEONotConfigured(...)
```

Every public method (`serp_organic_live`, `keyword_ideas`, `related_keywords`, `search_volume`, `ai_keyword_data`, `llm_responses`, `llm_mentions`) returns `self._post(...)` and nothing else. There is no method that reaches `urllib` without going through `_post`, so the guard cannot be bypassed. Confirmed by grep: `urlopen` appears once (line 85), inside `_post`, after the guard.

`is_configured()` (lines 56-59) requires BOTH vars non-empty: `return bool(login) and bool(password)`. Empty string is falsy, so `PASSWORD=""` correctly returns False. Tests confirm all three gating cases: unset, only-one-set, and empty-string (`test_dataforseo.py` lines 59-80).

The exception docstring explicitly states it is raised "before one [a network call], so catching it guarantees no money was spent and no socket was opened." `test_methods_raise_when_not_configured` swaps `urlopen` for a tripwire that raises `AssertionError` if hit, then asserts every method raises `DataForSEONotConfigured` instead — proving the gate fires before the network.

## 2. Offline default truly offline — PASS

- `rm -f data/aicmo.db && python3 run.py "why competitors all sound the same"` (no DATAFORSEO env vars) ran the full loop to `status: ad_live` with no network attempt and no error.
- `python3 -c "from engine.intelligence.intelligence import sweep_with_meta; print(sweep_with_meta('lumen-skin')['path'])"` printed `offline:stub`.

`sweep_with_meta` (intelligence.py lines 152-180) only takes the live branch inside `if dfs_client.is_configured():` wrapped in try/except that falls back to `_stub_seeds` on any exception. Default client is unconfigured, so it returns `offline:stub`.

## 3. Live path works when injected (no real network) — PASS

- `tests/test_dataforseo.py` monkeypatches `urllib.request.urlopen` with `_FakeResponse`/`_capture_urlopen`. No real socket.
- `tests/test_intelligence.py` and `tests/test_aeo.py` inject `_FakeConfiguredClient` (no urllib at all). Injecting a configured fake flips both modules to `live:dataforseo` and asserts the client was actually queried (`fake.calls` non-empty) — so the live path is exercised, not just declared.
- `_FakeUnconfiguredClient` raises `AssertionError` if its data methods are called, proving the unconfigured path never queries.
- No test references a real host except one URL-prefix assertion (`test_dataforseo.py:162`, asserting the Request's `full_url` starts with the base URL — not a call).
- `python3 -m pytest -q`: **78 passed** in 1.21s (147 deprecation warnings, all pre-existing `datetime.utcnow()`).

## 4. Secret safety — PASS

- Repo-wide grep for hardcoded login/password/token/api_key (excluding `os.environ`/`getenv`/examples/placeholders): no matches.
- `.env` is gitignored (`.gitignore` line 2: `.env`) and `git ls-files` confirms `.env` is NOT tracked.
- `.env.example` contains only empty values: `DATAFORSEO_LOGIN=` and `DATAFORSEO_PASSWORD=` (with explanatory comments, no real creds).
- Test fixtures use obvious fakes (`user@example.com` / `secret-pass`), never real credentials.

## 5. Auth header correctness — PASS

`_auth_header()` (lines 61-64): `"Basic " + base64.b64encode(f"{login}:{password}".encode("utf-8")).decode("ascii")` — correct `base64(login:password)` Basic auth. `_post` (line 79) builds the body as `json.dumps([payload])` — a JSON array wrapping the single task object, matching the DataForSEO convention. Both are asserted by `test_basic_auth_header_built_from_env` and `test_payload_is_json_array`.

## 6. Brief fidelity — PASS (with minor gap)

Build plan items 1-6 all present: stdlib client with `is_configured()` + single `_post` (1), SEO wired into intelligence with path logging (2), new `engine/aeo/aeo.py` with `ai_visibility_report` writing to `outputs/reports/` plus offline fallback (3), new `ai-cmo-aeo.md` command (4), mocked tests with no network (5), README + `.env.example` updated (6).

**Gap (non-blocking):** The brief's endpoint list names three endpoints with no corresponding client method:
- `dataforseo_labs/google/ranked_keywords/live`
- `dataforseo_labs/google/serp_competitors/live`
- `ai_optimization/gemini/llm_scraper/live` (Gemini scraper, the "budget option")

Implemented methods cover SERP organic, keyword_ideas, related_keywords, search_volume, ai_keyword_data, llm_responses, llm_mentions. The build plan says "typed methods for each SEO and AEO endpoint above," so these three are technically owed. They are not used by the current intelligence/AEO paths, so absence does not break anything shipped. Recommend either adding them or trimming the brief's endpoint list to match scope.

## 7. Voice (em dashes) — PASS

`grep -rn "—"` across new/changed files:
- `.claude/commands/ai-cmo-aeo.md`: 0
- `README.md`: 0
- generated report `outputs/reports/lumen-skin-aeo-visibility.md`: 0

The 12 em dashes found by the broad grep are all inside `docs/integrations/dataforseo-brief.md` — the pre-existing spec, not generated output. The AEO module enforces "No em dashes in generated markdown" and two tests assert `"—" not in text`. **Em-dash count in generated/changed deliverables: 0.**

## 8. Watch for silence — PASS

`write_ai_visibility_report('lumen-skin')` (offline) wrote a real 1256-byte file to `outputs/reports/lumen-skin-aeo-visibility.md` with a Summary table, per-query detail rows, and an explicit `Data source: Offline deterministic mock (...set DataForSEO credentials to go live)` line plus `Path: offline:stub`. No silent success: the report always states its data source and path, and `test_write_report_creates_nonempty_markdown_offline` asserts the file exists and `text.strip()` is non-empty. The intelligence layer also tags every seed with its source (`stub:` vs `live:dataforseo`) and returns `path` in `sweep_with_meta`, so no path "pretends" to be live.

---

## Minor observations (non-blocking, no fix required)

1. **Test nit, `test_dataforseo.py:208-213`** (`test_post_returns_parsed_json`): calls `_capture_urlopen({}, {...})` passing `{}` as the `captured` dict positionally, so nothing is captured. The test still passes because it only asserts the parsed return value. Harmless; could pass `captured={}` by name or drop the unused arg for clarity.
2. **Brief endpoint gap** (see Check 6): add `ranked_keywords`, `serp_competitors`, `gemini/llm_scraper` methods, or align the brief.

## Single most important fix

None blocking. If one item is actioned: close the Check 6 brief gap — implement the three missing endpoint methods (`ranked_keywords`, `serp_competitors`, `gemini/llm_scraper`) or trim them from the brief so spec and code agree.
