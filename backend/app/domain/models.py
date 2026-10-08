"""Validated bank and product models matching the ``banks`` and ``products`` tables."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

Identifier = Annotated[
    str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=200)
]
Name = Annotated[str, Field(min_length=1, max_length=200)]


class ProductCategory(StrEnum):
    FD = "FD"


class ProductStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISCONTINUED = "DISCONTINUED"


class BankStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class _Row(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @classmethod
    def from_row(cls, row: dict):
        """Build from a catalogue row; columns not in the table are ignored."""
        return cls.model_validate(row)


class Bank(_Row):
    id: Identifier
    name: Name
    website: HttpUrl | None = None
    country: str = Field(default="IN", pattern=r"^[A-Z]{2}$")
    status: BankStatus = BankStatus.ACTIVE


class Product(_Row):
    id: Identifier
    bank_id: Identifier
    category: ProductCategory
    name: Name
    description: str | None = None
    status: ProductStatus = ProductStatus.ACTIVE

    @field_validator("category", "status", mode="before")
    @classmethod
    def _upper(cls, value):
        return value.upper() if isinstance(value, str) else value
