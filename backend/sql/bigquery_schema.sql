-- Applied by `python -m scripts.create_bigquery_dataset` from backend/.
-- Project, dataset, and location are loaded from backend/.env via app.config.
CREATE SCHEMA IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{BIGQUERY_DATASET}}` OPTIONS(location="{{BIGQUERY_LOCATION}}");

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{BIGQUERY_DATASET}}.banks` (
  id STRING NOT NULL,
  name STRING NOT NULL,
  website STRING,
  country STRING NOT NULL,
  status STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{BIGQUERY_DATASET}}.products` (
  id STRING NOT NULL,
  bank_id STRING NOT NULL,
  category STRING NOT NULL,
  name STRING NOT NULL,
  description STRING,
  status STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{BIGQUERY_DATASET}}.product_rates` (
  id STRING NOT NULL,
  product_id STRING NOT NULL,
  rate FLOAT64 NOT NULL,
  rate_type STRING NOT NULL,
  min_amount FLOAT64,
  max_amount FLOAT64,
  tenure_months INT64,
  tenure_min_months INT64,
  tenure_max_months INT64,
  compounding_frequency INT64,
  payout_type STRING NOT NULL,
  effective_from DATE,
  effective_to DATE,
  source_id STRING,
  verification_status STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{BIGQUERY_DATASET}}.product_conditions` (
  id STRING NOT NULL,
  product_id STRING NOT NULL,
  condition_type STRING NOT NULL,
  condition_value STRING NOT NULL,
  source_id STRING,
  verification_status STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{BIGQUERY_DATASET}}.sources` (
  id STRING NOT NULL,
  product_id STRING NOT NULL,
  source_type STRING NOT NULL,
  url STRING NOT NULL,
  title STRING NOT NULL,
  document_uri STRING,
  retrieved_at TIMESTAMP NOT NULL,
  verified_at TIMESTAMP,
  effective_from DATE,
  effective_to DATE,
  content_hash STRING,
  status STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{BIGQUERY_DATASET}}.verification_records` (
  id STRING NOT NULL,
  product_id STRING NOT NULL,
  field_name STRING NOT NULL,
  observed_value STRING NOT NULL,
  normalized_value STRING NOT NULL,
  source_id STRING NOT NULL,
  confidence STRING NOT NULL,
  status STRING NOT NULL,
  checked_at TIMESTAMP NOT NULL,
  notes STRING
);

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{BIGQUERY_DATASET}}.source_conflicts` (
  id STRING NOT NULL,
  product_id STRING NOT NULL,
  field_name STRING NOT NULL,
  source_a STRING NOT NULL,
  value_a STRING NOT NULL,
  source_b STRING NOT NULL,
  value_b STRING NOT NULL,
  status STRING NOT NULL,
  resolved_value STRING,
  resolved_at TIMESTAMP,
  resolution_notes STRING
);

-- Research evidence is deliberately isolated from the canonical catalogue.
CREATE SCHEMA IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{RAG_DATASET}}` OPTIONS(location="{{BIGQUERY_LOCATION}}");

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{RAG_DATASET}}.source_documents` (
  document_id STRING NOT NULL,
  canonical_url STRING NOT NULL,
  title STRING NOT NULL,
  publisher STRING,
  domain STRING NOT NULL,
  document_type STRING NOT NULL,
  published_at TIMESTAMP,
  effective_from DATE,
  effective_to DATE,
  retrieved_at TIMESTAMP NOT NULL,
  content_hash STRING NOT NULL,
  source_status STRING NOT NULL,
  verification_status STRING NOT NULL,
  ingestion_status STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{RAG_DATASET}}.source_chunks` (
  chunk_id STRING NOT NULL,
  document_id STRING NOT NULL,
  chunk_index INT64 NOT NULL,
  excerpt STRING NOT NULL,
  product_category STRING,
  product_id STRING,
  source_status STRING NOT NULL,
  verification_status STRING NOT NULL,
  retrieved_at TIMESTAMP NOT NULL,
  content_hash STRING NOT NULL,
  embedding ARRAY<FLOAT64>,
  embedding_model STRING NOT NULL,
  embedding_dimensions INT64 NOT NULL
);

CREATE TABLE IF NOT EXISTS `{{BIGQUERY_PROJECT}}.{{RAG_DATASET}}.research_candidates` (
  candidate_id STRING NOT NULL,
  fact_type STRING NOT NULL,
  product_id STRING,
  candidate_value JSON NOT NULL,
  evidence_chunk_ids ARRAY<STRING>,
  source_url STRING NOT NULL,
  retrieved_at TIMESTAMP NOT NULL,
  verification_status STRING NOT NULL,
  validation_status STRING NOT NULL,
  conflict_ids ARRAY<STRING>,
  promotion_status STRING NOT NULL,
  content_hash STRING NOT NULL
);
