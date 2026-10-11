# Data model

The production schema is defined in [`backend/sql/bigquery_schema.sql`](../backend/sql/bigquery_schema.sql). BigQuery does not enforce declared relational constraints, so application/import code must keep references valid. The local JSON source is [`backend/data/fd-products.json`](../backend/data/fd-products.json); it is normalized by `LocalJsonCatalog` into the same runtime-shaped records.

## Catalogue entities

| Entity | Purpose | Important fields |
|---|---|---|
| `banks` | Institution identity | `id`, `name`, `website`, `country`, `status` |
| `products` | Offered financial product | `id`, `bank_id`, `category`, `name`, `description`, `status` |
| `product_rates` | Rate and eligibility slab | `product_id`, `rate`, amount bounds, tenure bounds, `payout_type`, compounding frequency, effective dates, `source_id`, verification status |
| `product_conditions` | Terms such as withdrawal or penalty | `product_id`, `condition_type`, `condition_value`, `source_id`, verification status |
| `sources` | Provenance record | URL/type/title, retrieval and verification timestamps, effective dates, content hash, active status |
| `verification_records` | A recorded check/observation | field, observed/normalized values, source, confidence, status, checked time, notes |
| `source_conflicts` | Two disagreeing source observations | field, both source IDs and values, status, optional resolution value/time/notes |

IDs are strings. References are declared as BigQuery `NOT ENFORCED` relationships. Source metadata is attached to each financial fact through `source_id`; important facts require a URL, retrieval/verification dates, effective period and confidence/status.

## Relationships

```text
banks 1 ── * products
products 1 ── * product_rates
products 1 ── * product_conditions
products 1 ── * sources
sources 1 ── * rates / conditions / verification_records
source_conflicts ── product + source_a + source_b
```

## Runtime and session records

Runtime catalog objects are assembled with nested `bank`, `rates`, `conditions`, `sources`, and `conflicts`. `Product` and `Bank` Pydantic models validate the core identity rows. Decision-session records store the owner UID, extracted requirements, comparison results and missing-information list; they do not store the original query. Local sessions exist only in process memory. Production sessions are stored in Firestore.

## Curation rules

The import script previews and upserts catalogue records; it does not delete old records. Resolve source conflicts explicitly using the local data's `conflict_resolutions` entries, requiring a selected observed value and notes. Do not seed plausible-looking rates: only manually reviewed, sourced values belong in the catalogue. See [verification system](verification-system.md).
