"""Compatibility exports for focused domain modules.

New code should import directly from the responsible ``app.domain`` module.
"""

from app.domain.catalog import product_payload
from app.domain.comparison import compare_products
from app.domain.identifiers import new_id
from app.domain.input import extract_requirements, redact_sensitive_input
from app.domain.sources import freshness, rate_is_usable

__all__ = [
    "compare_products",
    "extract_requirements",
    "freshness",
    "new_id",
    "product_payload",
    "rate_is_usable",
    "redact_sensitive_input",
]
