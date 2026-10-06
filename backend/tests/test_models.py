import pytest
from pydantic import ValidationError

from app.domain.models import Bank, BankStatus, Product, ProductCategory, ProductStatus
from app.repositories import bigquery as bigquery_module
from app.repositories.local_json import LocalJsonCatalog

# Columns of the `banks` and `products` tables in sql/bigquery_schema.sql.
BANK_COLUMNS = {"id", "name", "website", "country", "status"}
PRODUCT_COLUMNS = {"id", "bank_id", "category", "name", "description", "status"}


def test_bank_and_product_rows_match_table_columns():
    bank = Bank(id="hdfc-bank", name="HDFC Bank", website="https://www.hdfcbank.com")
    product = Product(
        id="hdfc-bank-fixed-deposit",
        bank_id=bank.id,
        category="fd",
        name="Fixed Deposit",
    )

    assert set(bank.to_row()) == BANK_COLUMNS
    assert set(product.to_row()) == PRODUCT_COLUMNS
    assert bank.to_row()["country"] == "IN"
    assert product.category is ProductCategory.FD
    assert product.status is ProductStatus.ACTIVE
    assert Product.from_row(product.to_row()) == product


def test_from_row_ignores_joined_and_nested_columns():
    product = Product.from_row(
        {
            "id": "sbi-fd",
            "bank_id": "sbi",
            "category": "FD",
            "name": "FD",
            "status": "active",
            "rates": [{"id": "r1"}],
            "bank_name": "State Bank of India",
        }
    )

    assert set(product.to_row()) == PRODUCT_COLUMNS


@pytest.mark.parametrize(
    "changes",
    [
        {"id": "HDFC Bank"},
        {"bank_id": ""},
        {"name": "   "},
        {"category": "CRYPTO"},
        {"status": "PENDING"},
    ],
)
def test_invalid_products_are_rejected(changes):
    row = {"id": "hdfc-bank-fd", "bank_id": "hdfc-bank", "category": "FD", "name": "FD"}

    with pytest.raises(ValidationError):
        Product.from_row({**row, **changes})


@pytest.mark.parametrize(
    "changes", [{"country": "India"}, {"website": "not a url"}, {"status": "CLOSED"}]
)
def test_invalid_banks_are_rejected(changes):
    with pytest.raises(ValidationError):
        Bank(**{"id": "sbi", "name": "SBI", **changes})


def test_local_catalog_banks_can_be_queried_and_own_every_product():
    catalog = LocalJsonCatalog()
    banks = catalog.list_banks()
    products = catalog.list_products(category="FD", status="ACTIVE")

    assert {bank.name for bank in banks} >= {"State Bank of India", "HDFC Bank"}
    assert catalog.get_bank("state-bank-of-india").name == "State Bank of India"
    assert catalog.get_bank("missing") is None
    for product in products:
        bank = catalog.get_bank(product["bank_id"])
        assert bank is not None and bank.name == product["bank"]
        Product.from_row(product)


class _FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []

    def query(self, sql, job_config=None, location=None):
        self.queries.append((sql, job_config))
        rows = self.rows

        class _Job:
            def result(self):
                return [dict(row) for row in rows]

        return _Job()


def test_bigquery_repository_returns_validated_banks(monkeypatch):
    monkeypatch.setattr(bigquery_module, "BIGQUERY_PROJECT", "test-project")
    client = _FakeClient(
        [
            {
                "id": "sbi",
                "name": "State Bank of India",
                "website": None,
                "country": "IN",
                "status": "ACTIVE",
            }
        ]
    )
    repository = bigquery_module.BigQueryRepository(client=client)

    banks = repository.list_banks()

    assert banks == [Bank(id="sbi", name="State Bank of India")]
    assert banks[0].status is BankStatus.ACTIVE
    assert "test-project.bankwise.banks" in client.queries[0][0]
    assert "@status" in client.queries[0][0]
    assert repository.get_bank("sbi").name == "State Bank of India"


def test_bigquery_repository_get_bank_returns_none_when_missing(monkeypatch):
    monkeypatch.setattr(bigquery_module, "BIGQUERY_PROJECT", "test-project")
    repository = bigquery_module.BigQueryRepository(client=_FakeClient([]))

    assert repository.get_bank("missing") is None
