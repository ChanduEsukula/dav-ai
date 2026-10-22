"""Ephemeral report identifiers; no accounts or persistence."""
import unicodedata
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class PharmaceuticalReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    product_id: str = Field(min_length=1, max_length=512)
    name: str = Field(min_length=1, max_length=100)
    age: StrictInt | None = Field(default=None, ge=0, le=120)

    @field_validator("name", "product_id")
    @classmethod
    def plain_text(cls, value):
        if not value.strip() or any(unicodedata.category(c).startswith("C") for c in value):
            raise ValueError("Use nonblank text without control characters")
        return value
