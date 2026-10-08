from app.domain.comparison import compare_products
from app.repositories.local_json import LocalJsonCatalog


def test_compare_products_generates_tradeoff_matrix_and_summary():
    catalog = LocalJsonCatalog()
    product_ids = [p["id"] for p in catalog.list_products(category="FD", status="ACTIVE")]

    result = compare_products(catalog, product_ids, amount=500000, tenure=24)

    assert "products" in result
    calculated = [p for p in result["products"] if p.get("calculation")]
    assert len(calculated) >= 2

    # Verify best item has gains and flag
    best_item = calculated[0]
    assert best_item["tradeoff"]["is_highest_calculated_maturity"] is True
    assert best_item["tradeoff"]["maturity_difference_vs_highest"] == 0.0
    assert len(best_item["tradeoff"]["gains"]) >= 1

    # Verify second item has give-up with positive difference
    second_item = calculated[1]
    assert second_item["tradeoff"]["is_highest_calculated_maturity"] is False
    assert second_item["tradeoff"]["maturity_difference_vs_highest"] > 0
    assert any("lower" in gu for gu in second_item["tradeoff"]["give_ups"])

    # Verify overarching trade-off summary exists
    assert result["tradeoff_summary"] is not None
    assert "maturity" in result["tradeoff_summary"].lower()
