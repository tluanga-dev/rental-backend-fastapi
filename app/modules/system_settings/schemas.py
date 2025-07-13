from pydantic import BaseModel, Field
from typing import Optional, List


class CurrencyConfig(BaseModel):
    """Schema for currency configuration."""
    currency_code: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    symbol: str = Field(..., description="Currency symbol")
    description: str = Field(..., description="Currency description")
    is_default: bool = Field(default=True, description="Is this the default currency")


class CurrencyUpdateRequest(BaseModel):
    """Schema for updating currency configuration."""
    currency_code: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    description: Optional[str] = Field(None, description="Currency description")


class SupportedCurrency(BaseModel):
    """Schema for supported currencies."""
    code: str = Field(..., description="Currency code")
    name: str = Field(..., description="Currency name")
    symbol: str = Field(..., description="Currency symbol")