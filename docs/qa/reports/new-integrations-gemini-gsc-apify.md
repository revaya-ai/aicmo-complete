# QA Audit: Gemini, GSC, Apify integrations

Independent QA. Auditor did not build this code. Goal: find SILENCE and security holes, not confirm success.

Date: 2026-06-20
Reference gold standard: `engine/integrations/dataforseo.py`, `engine/integrations/placid.py`

## Verdict: NO FAILS FOUND

All three new integrations match the established credential-gated, stdlib-only, offline-default pattern. Full suite green, end-to-end loop reaches `ad_live` offline.

## Per-check results

### A. Credential gate is unbypassable — PASS
- Gemini: `is_configured()` = `bool(self._key())`, handles unset + empty. Gate raised in `_post` BEFORE any urllib call. `gemini.py:60-62`, `gemini.py:72-76` (raise) precedes `gemini.py:82` (urlopen).
- GSC: requires BOTH creds: `bool(self._token()) and bool(self._site_url())`. `gsc.py:70-72`; raise at `gsc.py:85-89` before urlopen `gsc.py:95`. Tests cover all 4 negative cases. `tests/test_gsc.py:58-78`.
- Apify: `bool(self._token())`. `apify.py:57-59`; raise `apify.py:72-76` before urlopen `apify.py:82`.

### B. No network in tests / offline by default — PASS
- Every live-path test monkeypatches `urllib.request.urlopen`: gemini 16, gsc 13, apify 13 references. No `socket`/`requests`/`http.client` in any test.
- Unconfigured render falls back: `render.py:279-280` (not configured -> False) then `run()` falls through to PIL `render.py:392` then stdlib placeholder `render.py:395+`.
- Unconfigured intelligence returns `offline:stub`. `intelligence.py:314`. Verified by `tests/test_intelligence.py:39,90-94,231-238`.

### C. No secret leakage — PASS
- Gemini uses `x-goog-api-key` header `gemini.py:80`. GSC + Apify use `Authorization: Bearer` `gsc.py:93`, `apify.py:80`. No `token=`/`key=`/`password=` in any URL build (grep returned nothing). No `print`/`logging` of secrets. Apify test asserts `"token=" not in url` `tests/test_apify.py:114`.

### D. Request shape is real, not faked — PASS
- Gemini: POST `models/<model>:generateContent`, text part body, decodes `inlineData.data` via `base64.b64decode` to real bytes. `gemini.py:96-106`, extract `gemini.py:108-120`. Test confirms exact raw bytes round-trip `tests/test_gemini.py:165-173`.
- GSC: POST searchanalytics, Bearer header, JSON body `gsc.py:90-96`.
- Apify: POST `acts/{id}/run-sync-get-dataset-items`, Bearer, returns list `apify.py:87-100`.

### E. No silent success — PASS
- `_render_with_gemini` returns False on not-configured, empty data, or any exception; never writes garbage while reporting success. `render.py:279-280, 291-292, 296-297`. Caller only prints "backend: gemini" when `drawn` is True `render.py:332-333, 385-386`.
- Intelligence live paths wrapped in try/except; on error the source is skipped, sweep falls back to stub, no pretending. `intelligence.py:283-309`. Path label honestly composes from sources that actually ran `intelligence.py:311-314`.

### F. Back-compat preserved — PASS
- DataForSEO-only path is EXACTLY `live:dataforseo`; nothing configured is EXACTLY `offline:stub`. `intelligence.py:311-314`. Asserted by `tests/test_intelligence.py:102, 220-228, 231-238`. All-three composes `live:dataforseo+gsc+apify` `tests/test_intelligence.py:213`. All pass.

### G. db.py FROZEN — PASS
- `git diff --stat -- '*db.py'` empty; no db.py in `git status --porcelain`.

### H. No em dashes / emojis — PASS
- Scanned all 5 new/modified files. Zero em dashes, en dashes, or emoji.

## Suite + loop
- `python -m pytest -q`: **150 passed**, 183 warnings (only `datetime.utcnow` DeprecationWarnings, pre-existing, unrelated).
- `python run.py "simple skincare routine for sensitive skin"` offline (all integration env vars unset): final status **`ad_live`**, exit 0. Render used stdlib/PIL default (no AICMO_RENDER), intelligence stayed on stub.

## Minor (non-blocking, not a FAIL)
- `intelligence.py:19` docstring references env var `GSC_CREDENTIALS`, but the actual GSC env vars are `GSC_ACCESS_TOKEN` and `GSC_SITE_URL`. Stale doc comment only; code and gate are correct. Recommend a one-word doc fix on next touch.
