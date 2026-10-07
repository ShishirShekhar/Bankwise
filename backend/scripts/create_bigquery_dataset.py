"""Create the configured BigQuery dataset if it does not already exist.

Run from ``backend/`` with Google Cloud ADC credentials configured:
``python -m scripts.create_bigquery_dataset``.
"""

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


if __name__ == "__main__":
    main()
