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
