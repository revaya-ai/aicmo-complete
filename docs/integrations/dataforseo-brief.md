# Integration Brief: DataForSEO (SEO + AEO)

> Approved scope: both SEO and AEO. Approved mode: credential-ready, no live calls yet (offline stub stays the default; the integration activates when credentials are present). This brief is the spec for the build.

## Why

The reference architecture's intelligence layer requires SEO, GEO, and AEO signals feeding the strategist (component C), plus AEO reporting in the dashboard (component J). Today both are deterministic offline stubs. DataForSEO provides the real data behind one account.

## What we use

### SEO (feeds the Intelligence layer)
- **SERP API** `serp/google/organic/live/advanced` — real-time Google SERP. Live about $0.002 per search, standard queue $0.0006.
- **DataForSEO Labs** `dataforseo_labs/google/keyword_ideas/live`, `related_keywords/live`, `ranked_keywords/live`, `serp_competitors/live` — keyword research and competitor intelligence. About $0.01 per task plus $0.0001 per keyword.
- **Keywords Data** `keywords_data/google_ads/search_volume/live` — real search volume.

### AEO (new module plus report)
- **AI Keyword Data** `ai_optimization/ai_keyword_data/keywords_search_volume/live` — AI search volume, how people phrase queries inside AI tools, 12-month trend. About $0.0001 per keyword.
- **LLM Mentions** — whether the client brand is mentioned or cited in LLM answers, with sentiment. AI visibility tracking.
- **LLM Responses / LLM Scraper** `ai_optimization/chat_gpt/llm_responses/live`, `ai_optimization/gemini/llm_scraper/live` — ask the client's target questions across ChatGPT and Gemini through one interface and see if the client is cited. About $0.0006 plus the LLM's own cost (Scraper is the budget option).

## Auth and cost
- HTTP Basic Auth. Base URL `https://api.dataforseo.com/v3/`. Credentials from env: `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`. Never committed.
- Pay-as-you-go, $50 minimum deposit. All calls cheap. The build makes zero live calls until credentials are set.

## Build plan

1. `engine/integrations/dataforseo.py` — a stdlib client (urllib + base64 Basic Auth). `is_configured()` checks env. One `_post(endpoint, payload)` helper. Typed methods for each SEO and AEO endpoint above. When not configured, methods signal "not configured" so callers fall back to the offline stub. No live call in tests or CI.
2. Wire SEO into `engine/intelligence/intelligence.py` — when configured, generate seed ideas and keyword targets from Keyword Ideas plus SERP, grounded in the client pillars. When not configured, keep the current deterministic offline seeds. Log which path ran (no silent pretending).
3. New `engine/aeo/aeo.py` — `ai_visibility_report(client)`: for the client's target questions and keywords (from positioning and strategy), pull AI Keyword Data plus LLM Mentions, write an AEO visibility report to `outputs/reports/`. Offline deterministic fallback so it runs for anyone.
4. New command `.claude/commands/ai-cmo-aeo.md` — run the AEO visibility report. Update `ai-cmo-intel.md` to note the live SEO path.
5. Tests in `tests/` — mock the HTTP layer. Assert the client builds the right request and auth header, the intelligence module uses live data when the client is injected, and the AEO report renders. No network.
6. Docs — README and CLAUDE.md updated with the new command, the env vars, and the cost note. `.env.example` gets the two vars if writable, otherwise the README documents them.

## Guardrails
- `db.py` frozen. Offline default path stays stdlib-only with no keys. Real calls only behind credentials.
- No em dashes in any new markdown. Keep the loop green and all tests passing.
- Credentials never printed or committed.
