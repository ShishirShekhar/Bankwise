"""Create the configured BigQuery dataset and Bankwise tables."""

import re
from pathlib import Path

from google.cloud import bigquery

from app.config import BIGQUERY_DATASET, BIGQUERY_LOCATION, BIGQUERY_PROJECT


def main() -> None:
    if not BIGQUERY_PROJECT:
        raise SystemExit("Set BIGQUERY_PROJECT or GOOGLE_CLOUD_PROJECT in backend/.env")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", BIGQUERY_PROJECT):
        raise SystemExit("BIGQUERY_PROJECT contains invalid characters")
    if not re.fullmatch(r"[A-Za-z0-9_]+", BIGQUERY_DATASET):
        raise SystemExit("BIGQUERY_DATASET contains invalid characters")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", BIGQUERY_LOCATION):
        raise SystemExit("BIGQUERY_LOCATION contains invalid characters")

    sql_path = Path(__file__).resolve().parents[1] / "sql" / "bigquery_schema.sql"
    sql = sql_path.read_text(encoding="utf-8")
    substitutions = {
        "{{BIGQUERY_PROJECT}}": BIGQUERY_PROJECT,
        "{{BIGQUERY_DATASET}}": BIGQUERY_DATASET,
        "{{BIGQUERY_LOCATION}}": BIGQUERY_LOCATION,
    }
    for placeholder, value in substitutions.items():
        sql = sql.replace(placeholder, value)

    client = bigquery.Client(project=BIGQUERY_PROJECT, location=BIGQUERY_LOCATION)
    client.query(sql, location=BIGQUERY_LOCATION).result()
    print(
        f"Created or confirmed BigQuery dataset "
        f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET} in {BIGQUERY_LOCATION}."
    )


if __name__ == "__main__":
    main()
