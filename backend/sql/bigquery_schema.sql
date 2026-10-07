-- Run with `bq query --use_legacy_sql=false < bigquery_schema.sql` after
-- selecting the project/dataset; replace `YOUR_PROJECT.bankwise` as needed.
--
-- Tables are ordered so every referenced table is created first. BigQuery does
-- not enforce primary/foreign keys; they document relationships and help the
-- query optimizer. Application code must still validate references.
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT.bankwise` OPTIONS(location="us-central1");

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.bankwise.banks` (
  id STRING NOT NULL,
  name STRING NOT NULL,
  website STRING,
  country STRING NOT NULL,
  status STRING NOT NULL,
  PRIMARY KEY (id) NOT ENFORCED
);

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.bankwise.products` (
  id STRING NOT NULL,
  bank_id STRING NOT NULL,
  category STRING NOT NULL,
  name STRING NOT NULL,
  description STRING,
  status STRING NOT NULL,
  PRIMARY KEY (id) NOT ENFORCED,
  FOREIGN KEY (bank_id) REFERENCES `YOUR_PROJECT.bankwise.banks`(id) NOT ENFORCED
);

-- Provenance for every financial fact: where it came from, when it was
-- retrieved and verified, and the period the source says it applies to.
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.bankwise.sources` (
  id STRING NOT NULL,
  product_id STRING NOT NULL,
  source_type STRING NOT NULL,
  url STRING NOT NULL,
  title STRING NOT NULL,
  reference STRING,
  document_uri STRING,
  retrieved_at TIMESTAMP NOT NULL,
  verified_at TIMESTAMP,
  effective_from DATE,
  effective_to DATE,
  content_hash STRING,
  status STRING NOT NULL,
  PRIMARY KEY (id) NOT ENFORCED,
  FOREIGN KEY (product_id) REFERENCES `YOUR_PROJECT.bankwise.products`(id) NOT ENFORCED
);

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.bankwise.product_rates` (
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
  calculation_source_url STRING,
  effective_from DATE,
  effective_to DATE,
  source_id STRING,
  verification_status STRING NOT NULL,
  PRIMARY KEY (id) NOT ENFORCED,
  FOREIGN KEY (product_id) REFERENCES `YOUR_PROJECT.bankwise.products`(id) NOT ENFORCED,
  FOREIGN KEY (source_id) REFERENCES `YOUR_PROJECT.bankwise.sources`(id) NOT ENFORCED
);

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.bankwise.product_conditions` (
  id STRING NOT NULL,
  product_id STRING NOT NULL,
  condition_type STRING NOT NULL,
  condition_value STRING NOT NULL,
  source_id STRING,
  verification_status STRING NOT NULL,
  PRIMARY KEY (id) NOT ENFORCED,
  FOREIGN KEY (product_id) REFERENCES `YOUR_PROJECT.bankwise.products`(id) NOT ENFORCED,
  FOREIGN KEY (source_id) REFERENCES `YOUR_PROJECT.bankwise.sources`(id) NOT ENFORCED
);

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.bankwise.verification_records` (
  id STRING NOT NULL,
  product_id STRING NOT NULL,
  field_name STRING NOT NULL,
  observed_value STRING NOT NULL,
  normalized_value STRING NOT NULL,
  source_id STRING NOT NULL,
  confidence STRING NOT NULL,
  status STRING NOT NULL,
  checked_at TIMESTAMP NOT NULL,
  notes STRING,
  PRIMARY KEY (id) NOT ENFORCED,
  FOREIGN KEY (product_id) REFERENCES `YOUR_PROJECT.bankwise.products`(id) NOT ENFORCED,
  FOREIGN KEY (source_id) REFERENCES `YOUR_PROJECT.bankwise.sources`(id) NOT ENFORCED
);

-- Both observations are kept; a conflicting value must not be used as
-- authoritative while status is OPEN.
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.bankwise.source_conflicts` (
  id STRING NOT NULL,
  product_id STRING NOT NULL,
  field_name STRING NOT NULL,
  source_a STRING NOT NULL,
  value_a STRING NOT NULL,
  source_b STRING NOT NULL,
  value_b STRING NOT NULL,
  source_b_url STRING,
  note STRING,
  status STRING NOT NULL,
  detected_at TIMESTAMP NOT NULL,
  resolved_value STRING,
  resolved_at TIMESTAMP,
  resolution_notes STRING,
  PRIMARY KEY (id) NOT ENFORCED,
  FOREIGN KEY (product_id) REFERENCES `YOUR_PROJECT.bankwise.products`(id) NOT ENFORCED,
  FOREIGN KEY (source_a) REFERENCES `YOUR_PROJECT.bankwise.sources`(id) NOT ENFORCED,
  FOREIGN KEY (source_b) REFERENCES `YOUR_PROJECT.bankwise.sources`(id) NOT ENFORCED
);
