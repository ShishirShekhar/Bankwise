import json

from app.domain.comparison import compare_products
from app.domain.catalog import product_payload
from app.repositories.local_json import LocalJsonCatalog


def test_local_catalog_loads_products_and_source_references():
    catalog = LocalJsonCatalog()

    products = catalog.list_products(category="FD", status="ACTIVE")
    hdfc = next(p for p in products if p["bank"] == "HDFC Bank")

    assert len(products) == 5
    assert hdfc["rates"]
    assert hdfc["sources"][0]["reference"] == "HDFC Bank official FD interest-rate page"


def test_local_product_payload_is_json_serializable_for_adk_tools():
    catalog = LocalJsonCatalog()
    product = catalog.list_products(category="FD", status="ACTIVE")[0]

    payload = product_payload(product, catalog)

    json.dumps(payload)


def test_local_rate_ranges_select_one_rate_for_two_years_and_surface_conflicts():
    catalog = LocalJsonCatalog()
    products = catalog.list_products(category="FD", status="ACTIVE")
    result = compare_products(
        catalog,
        [product["id"] for product in products],
        amount=500000,
        tenure=24,
    )

    assert all(item["eligible"] for item in result["products"])
    pnb = next(item for item in result["products"] if item["product"]["bank"] == "Punjab National Bank")
    assert pnb["calculation"] is None
    assert pnb["product"]["conflicts"]


def test_local_data_does_not_calculate_without_payout_and_compounding_terms():
    catalog = LocalJsonCatalog()
    products = catalog.list_products(category="FD", status="ACTIVE")
    result = compare_products(
        catalog,
        [product["id"] for product in products],
        amount=100000,
        tenure=12,
    )

    assert result["products"]
    assert all(item["calculation"] is None for item in result["products"])
    assert all(
        item["calculation_blocked_reason"]
        for item in result["products"]
        if item["eligible"]
    )


def test_tenure_without_rate_slab_is_reported_without_crashing():
    catalog = LocalJsonCatalog()
    products = catalog.list_products(category="FD", status="ACTIVE")

    result = compare_products(
        catalog,
        [product["id"] for product in products],
        amount=100000,
        tenure=6,
    )

    assert result["products"]
    assert all(not item["eligible"] for item in result["products"])
    assert result["warnings"]
