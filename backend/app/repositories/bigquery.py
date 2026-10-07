"""Read-only BigQuery repository for curated catalogue and verification data."""

import re
from typing import Any

from app.config import BIGQUERY_DATASET, BIGQUERY_LOCATION, BIGQUERY_PROJECT
from app.domain.models import Bank


class BigQueryRepository:
    def __init__(self, client=None):
        if not BIGQUERY_PROJECT:
            raise RuntimeError("Set BIGQUERY_PROJECT or GOOGLE_CLOUD_PROJECT")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", BIGQUERY_PROJECT) or not re.fullmatch(
            r"[A-Za-z0-9_]+", BIGQUERY_DATASET
        ):
            raise ValueError("Invalid BigQuery project or dataset identifier")
        if client is None:
            from google.cloud import bigquery

            client = bigquery.Client(
                project=BIGQUERY_PROJECT, location=BIGQUERY_LOCATION
            )
        self.client = client
        self.prefix = f"`{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}"
        self._source_cache = {}
        self._conflict_cache = {}
        self._product_cache = {}

    def _rows(
        self, table: str, where: str = "", params: list | None = None
    ) -> list[dict[str, Any]]:
        from google.cloud import bigquery

        sql = f"SELECT * FROM {self.prefix}.{table}` {where}"
        config = bigquery.QueryJobConfig(query_parameters=params or [])
        return [
            dict(row.items())
            for row in self.client.query(
                sql, job_config=config, location=BIGQUERY_LOCATION
            ).result()
        ]

    def _one(self, table: str, identifier: str) -> dict[str, Any] | None:
        from google.cloud import bigquery

        sql = f"SELECT * FROM {self.prefix}.{table}` WHERE id = @id LIMIT 1"
        config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("id", "STRING", identifier)]
        )
        rows = list(
            self.client.query(
                sql, job_config=config, location=BIGQUERY_LOCATION
            ).result()
        )
        return dict(rows[0].items()) if rows else None

    def list_banks(self, status: str = "ACTIVE") -> list[Bank]:
        from google.cloud import bigquery

        rows = self._rows(
            "banks",
            "WHERE status=@status ORDER BY name",
            [bigquery.ScalarQueryParameter("status", "STRING", status)],
        )
        return [Bank.from_row(row) for row in rows]

    def get_bank(self, bank_id: str) -> Bank | None:
        row = self._one("banks", bank_id)
        return Bank.from_row(row) if row else None

    def list_products(
        self, category: str = "FD", status: str = "ACTIVE"
    ) -> list[dict[str, Any]]:
        from google.cloud import bigquery

        sql = (
            f"SELECT p.*, b.name AS bank_name, b.website AS bank_website "
            f"FROM {self.prefix}.products` p JOIN {self.prefix}.banks` b ON b.id=p.bank_id "
            "WHERE p.category=@category AND p.status=@status ORDER BY b.name, p.name"
        )
        config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("category", "STRING", category.upper()),
                bigquery.ScalarQueryParameter("status", "STRING", status),
            ]
        )
        products = [
            self._hydrate(dict(row.items()))
            for row in self.client.query(
                sql, job_config=config, location=BIGQUERY_LOCATION
            ).result()
        ]
        for product in products:
            self._product_cache[product["id"]] = product
        return products

    def get_product(
        self,
        product_id: str,
        category: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any] | None:
        cached = self._product_cache.get(product_id)
        if cached is not None:
            if category is not None and cached.get("category") != category.upper():
                return None
            if status is not None and cached.get("status") != status:
                return None
            return cached
        from google.cloud import bigquery

        filters = ["p.id=@id"]
        params = [bigquery.ScalarQueryParameter("id", "STRING", product_id)]
        if category is not None:
            filters.append("p.category=@category")
            params.append(
                bigquery.ScalarQueryParameter("category", "STRING", category.upper())
            )
        if status is not None:
            filters.append("p.status=@status")
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status))
        sql = (
            f"SELECT p.*, b.name AS bank_name, b.website AS bank_website "
            f"FROM {self.prefix}.products` p JOIN {self.prefix}.banks` b ON b.id=p.bank_id "
            f"WHERE {' AND '.join(filters)} LIMIT 1"
        )
        rows = list(
            self.client.query(
                sql,
                job_config=bigquery.QueryJobConfig(query_parameters=params),
                location=BIGQUERY_LOCATION,
            ).result()
        )
        if not rows:
            return None
        product = self._hydrate(dict(rows[0].items()))
        self._product_cache[product_id] = product
        return product

    def _hydrate(self, product: dict[str, Any]) -> dict[str, Any]:
        from google.cloud import bigquery

        product_id = product["id"]
        params = [bigquery.ScalarQueryParameter("product_id", "STRING", product_id)]

        def related(table: str) -> list[dict[str, Any]]:
            sql = f"SELECT * FROM {self.prefix}.{table}` WHERE product_id=@product_id"
            return [
                dict(row.items())
                for row in self.client.query(
                    sql,
                    job_config=bigquery.QueryJobConfig(query_parameters=params),
                    location=BIGQUERY_LOCATION,
                ).result()
            ]

        product["bank"] = {
            "id": product["bank_id"],
            "name": product.pop("bank_name", None),
            "website": product.pop("bank_website", None),
        }
        product["rates"] = related("product_rates")
        product["conditions"] = related("product_conditions")
        product["sources"] = related("sources")
        for source in product["sources"]:
            self._source_cache[source["id"]] = source
        return product

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        if source_id not in self._source_cache:
            self._source_cache[source_id] = self._one("sources", source_id)
        return self._source_cache[source_id]

    def get_conflicts(
        self, product_id: str, field_name: str | None = None, status: str = "OPEN"
    ) -> list[dict[str, Any]]:
        cache_key = (product_id, status)
        if cache_key in self._conflict_cache:
            conflicts = self._conflict_cache[cache_key]
            return [
                conflict
                for conflict in conflicts
                if not field_name or conflict["field_name"] == field_name
            ]
        from google.cloud import bigquery

        filters = ["product_id=@product_id", "status=@status"]
        params = [
            bigquery.ScalarQueryParameter("product_id", "STRING", product_id),
            bigquery.ScalarQueryParameter("status", "STRING", status),
        ]
        sql = f"SELECT * FROM {self.prefix}.source_conflicts` WHERE {' AND '.join(filters)}"
        conflicts = [
            dict(row.items())
            for row in self.client.query(
                sql,
                job_config=bigquery.QueryJobConfig(query_parameters=params),
                location=BIGQUERY_LOCATION,
            ).result()
        ]
        self._conflict_cache[cache_key] = conflicts
        return [
            conflict
            for conflict in conflicts
            if not field_name or conflict["field_name"] == field_name
        ]

    def list_conflicts(self, status: str = "OPEN") -> list[dict[str, Any]]:
        from google.cloud import bigquery

        return self._rows(
            "source_conflicts",
            "WHERE status=@status",
            [bigquery.ScalarQueryParameter("status", "STRING", status)],
        )
