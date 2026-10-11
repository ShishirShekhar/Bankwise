# Verification system

Verification rules are implemented in `backend/app/domain/sources.py`; conflict detection and resolution are in `backend/app/domain/conflicts.py`. API payloads are shaped by `domain/catalog.py` and operations are exposed through `/api/verification/run` and `/api/conflicts`.

## Source checks

Official bank pages and PDFs have source authority `HIGH`; other source types are `MEDIUM`. Authority alone is insufficient. A source is downgraded to `LOW` if inactive, missing retrieval/verification dates, older than `SOURCE_MAX_AGE_DAYS` (default 90), not yet effective, or expired. The source's `verified_at`/`retrieved_at`, URL, type, title and effective period are exposed with facts.

Each rate or condition receives the worst applicable status:

| Status | Meaning | Calculation use |
|---|---|---|
| `HIGH` | Current official source, current fact, no applicable open conflict | Rates can be used |
| `MEDIUM` | Current non-official source | Not usable |
| `LOW` | Stale, inactive, unverified, or outside effective dates | Not usable |
| `CONFLICT` | An unresolved disagreement applies | Not usable |
| `MISSING` | No valid linked source | Not usable |

Stored verification status is also considered; only `HIGH` remains eligible for calculation.

## Conflicts

Local source observations are compared for the same product, field and rate band. Values are normalized (numeric rounding, or trimmed and case-folded text) before comparing. Disagreement creates an open conflict storing both source IDs and values. The system never silently selects one.

An open rate conflict blocks the affected band; a hand-recorded conflict without a band blocks all rates for that field. An open condition conflict marks the matching condition type. Conflict facts appear in product payloads and the conflict endpoint. A resolved conflict remains in history. Resolution must choose one of the observed values and include notes; unresolved or invalid resolution leaves it open.

## Operational boundaries

`POST /api/verification/run` evaluates metadata already stored; it does **not** crawl or retrieve external pages. Source recency therefore depends on a human curation/update process. The current catalogue marks some entries `verify_before_production`; such inactive sources cannot support calculations. Keep production data manually reviewed and refresh provenance before expiry.

Tests: `backend/tests/test_source_rules.py`, `backend/tests/test_conflicts.py`, and related import/catalog tests.
