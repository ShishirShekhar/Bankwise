"""Create the configured BigQuery dataset if it does not already exist.

Run from ``backend/`` with Google Cloud ADC credentials configured:
``python -m scripts.create_bigquery_dataset``.

After ensuring the dataset exists, this also applies the idempotent table DDL
from ``sql/bigquery_schema.sql``.
"""

from pathlib import Path

from google.cloud import bigquery

from app.config import BIGQUERY_DATASET, BIGQUERY_LOCATION, BIGQUERY_PROJECT


def main() -> None:
    if not BIGQUERY_PROJECT:
        raise SystemExit("Set BIGQUERY_PROJECT or GOOGLE_CLOUD_PROJECT in backend/.env")

    client = bigquery.Client(project=BIGQUERY_PROJECT, location=BIGQUERY_LOCATION)
    dataset_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = BIGQUERY_LOCATION
    client.create_dataset(dataset, exists_ok=True)
    print(f"BigQuery dataset ready: {dataset_id} ({BIGQUERY_LOCATION})")

    schema_path = Path(__file__).resolve().parents[1] / "sql" / "bigquery_schema.sql"
    schema = schema_path.read_text(encoding="utf-8")
    schema = schema.replace("{{BIGQUERY_PROJECT}}", BIGQUERY_PROJECT)
    schema = schema.replace("{{BIGQUERY_DATASET}}", BIGQUERY_DATASET)
    schema = schema.replace("{{BIGQUERY_LOCATION}}", BIGQUERY_LOCATION)
    statements = [statement.strip() for statement in schema.split(";")]
    statements = [statement for statement in statements if statement]

    for statement in statements:
        client.query(statement, location=BIGQUERY_LOCATION).result()

    print(f"BigQuery tables are ready in {dataset_id}")


if __name__ == "__main__":
    main()
