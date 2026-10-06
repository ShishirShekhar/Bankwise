"""Boundary tests for whole-month FD rate bands in the local catalogue.

Bands in ``data/fd-products.json`` are inclusive integer-month ranges. Each
case below maps a boundary month to the band the bank's official slab wording
places it in (``None`` means no sourced band covers that month):

- SBI: "1 Year to less than 2 years" (12-23), "2 years to less than 3 years"
  (24-35), "3 years to less than 5 years" (36-59).
- HDFC: "15 months to less than 18 months" (15-17), "21 months to 2 years" and
  "2 years 1 day to less than 3 years" (24-35).
- ICICI: "< 18 Months" (12-17), "18 Months to 2 Years" (18-24),
  "2 Years 1 Day to 3 Years" (25-36).
- Bank of Baroda: "upto 2 Years" (12-24), "Above 2 Years and upto 3 Years"
  (25-36), "Above 3 Years and upto 5 Years" (37-60).
- PNB: "667 Days to 2 Years" (12-24), ">2 to 3 Years" (25-36),
  ">3 Years to 1203 Days" / "1205 Days to 5 Years" (37-60).
"""

from itertools import pairwise

import pytest

from app.domain.catalog import product_payload
from app.domain.comparison import compare_products
from app.repositories.local_json import LocalJsonCatalog

SBI = "state-bank-of-india-retail-domestic-term-deposit"
HDFC = "hdfc-bank-regular-fixed-deposit"
ICICI = "icici-bank-regular-fixed-deposit"
BOB = "bank-of-baroda-domestic-term-deposit"
PNB = "punjab-national-bank-domestic-fixed-deposit"

BOUNDARY_CASES = [
    (SBI, 11, None),
    (SBI, 12, (12, 23)),
    (SBI, 23, (12, 23)),
    (SBI, 24, (24, 35)),
    (SBI, 35, (24, 35)),
    (SBI, 36, (36, 59)),
    (SBI, 59, (36, 59)),
    (SBI, 60, None),
    (HDFC, 11, None),
    (HDFC, 12, (12, 14)),
    (HDFC, 14, (12, 14)),
    (HDFC, 15, (15, 17)),
    (HDFC, 17, (15, 17)),
    (HDFC, 18, None),
    (HDFC, 23, None),
    (HDFC, 24, (24, 35)),
    (HDFC, 35, (24, 35)),
    (HDFC, 36, None),
    (ICICI, 11, None),
    (ICICI, 12, (12, 17)),
    (ICICI, 17, (12, 17)),
    (ICICI, 18, (18, 24)),
    (ICICI, 24, (18, 24)),
    (ICICI, 25, (25, 36)),
    (ICICI, 36, (25, 36)),
    (ICICI, 37, None),
    (BOB, 11, None),
    (BOB, 12, (12, 24)),
    (BOB, 24, (12, 24)),
    (BOB, 25, (25, 36)),
    (BOB, 36, (25, 36)),
    (BOB, 37, (37, 60)),
    (BOB, 60, (37, 60)),
    (BOB, 61, None),
    (PNB, 11, None),
    (PNB, 12, (12, 24)),
    (PNB, 24, (12, 24)),
    (PNB, 25, (25, 36)),
    (PNB, 36, (25, 36)),
    (PNB, 37, (37, 60)),
    (PNB, 60, (37, 60)),
    (PNB, 61, None),
]


@pytest.fixture(scope="module")
def catalog():
    return LocalJsonCatalog()


@pytest.mark.parametrize(("product_id", "tenure", "band"), BOUNDARY_CASES)
def test_boundary_month_selects_sourced_band(catalog, product_id, tenure, band):
    result = compare_products(catalog, [product_id], amount=100000, tenure=tenure)
    (item,) = result["products"]

    assert item["eligible"] is (band is not None)

    payload = product_payload(catalog.get_product(product_id), catalog, 100000, tenure)
    matched = [
        (rate["tenure_min_months"], rate["tenure_max_months"])
        for rate in payload["rates"]
        if rate["ineligibility_reason"] is None
    ]
    assert matched == ([band] if band else [])


def test_rate_bands_do_not_overlap_within_a_product(catalog):
    for product in catalog.list_products():
        bands = sorted(
            (rate["tenure_min_months"], rate["tenure_max_months"])
            for rate in product["rates"]
        )
        for (_, previous_max), (next_min, _) in pairwise(bands):
            assert previous_max < next_min, product["id"]


def test_rates_do_not_carry_text_derived_inclusivity_flags(catalog):
    for product in catalog.list_products():
        for rate in product["rates"]:
            assert "tenure_min_inclusive" not in rate
            assert "tenure_max_inclusive" not in rate
