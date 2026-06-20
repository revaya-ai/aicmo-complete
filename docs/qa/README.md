# QA — How this system is checked

This system is checked by independent QA agents, not by the agents that built it. The principle: the agent that checks is never the agent that built, and you watch for silence, not just errors. A component that is documented but absent, or a step that reports success while producing nothing real, is a failure even when nothing throws.

## The QA agents

Three independent auditors live in `.claude/agents/qa/`, each with its own charter and non-negotiables:

- **architecture-fidelity-auditor** — every component in `reference-architecture.md` exists and is genuinely wired, not faked or silently absent.
- **runs-for-anyone-auditor** — a stranger can clone the repo and run it offline from the README alone, and every success produces a real artifact.
- **brand-voice-fidelity-auditor** — voice discipline (no em dashes, no AI-slop), the human gate cannot be bypassed, and the repo is IP clean.

The source of truth they audit against is `reference-architecture.md`.

## Audit trail

The detailed reports in `reports/` are the raw audit output, kept as the record. The audits were run, they found real problems, the problems were fixed by a separate builder, and the system was re-verified green. Summary:

| Audit | First run | After fixes |
|-------|-----------|-------------|
| Architecture fidelity | FAIL (offline brain ignored client context; render produced a blank image; QC fabricated notes) | Fixed: brain loads the 6-layer context, render composites real text, QC reports only what it inspects |
| Runs for anyone | FAIL (3 silent successes: blank PNG passing QC; notion mirror not produced by the loop) | Fixed: PNG carries real text, the loop writes the notion mirror, artifacts verified non-empty |
| Brand and voice | FAIL (31 em dashes including the brand's own voice files; third-party names in a public repo) | Fixed: em dashes scrubbed from all product files, third-party names removed from source and prose |
| DataForSEO integration | PASS on all 8 checks (credential gate unbypassable, offline default, no secrets, no network in tests) | n/a |

Current state after fixes, independently re-verified: the loop reaches `ad_live`, all tests pass, zero em dashes in product files, zero third-party names in source.

## Re-run QA yourself

The reports are point-in-time. To re-audit after any change, dispatch each agent in `.claude/agents/qa/` against the repo (it must be a different agent than the one that made the change), and have it write a fresh report to `reports/`. Then fix every finding and re-verify the loop and the test suite before shipping.
