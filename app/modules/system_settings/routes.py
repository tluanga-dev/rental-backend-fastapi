from typing import List
from fastapi import APIRouter, HTTPException, status
from app.modules.system_settings.schemas import (
    CurrencyConfig, CurrencyUpdateRequest, SupportedCurrency
)


router = APIRouter(tags=["System Settings"])

# In-memory currency configuration (in production, this would be in database)
current_currency = CurrencyConfig(
    currency_code="INR",
    symbol="₹",
    description="Indian Rupee",
    is_default=True
)

# Supported currencies
SUPPORTED_CURRENCIES = [
    SupportedCurrency(code="INR", name="Indian Rupee", symbol="₹"),
    SupportedCurrency(code="USD", name="US Dollar", symbol="$"),
    SupportedCurrency(code="EUR", name="Euro", symbol="€"),
    SupportedCurrency(code="GBP", name="British Pound", symbol="£"),
    SupportedCurrency(code="JPY", name="Japanese Yen", symbol="¥"),
    SupportedCurrency(code="CAD", name="Canadian Dollar", symbol="C$"),
    SupportedCurrency(code="AUD", name="Australian Dollar", symbol="A$"),
    SupportedCurrency(code="CNY", name="Chinese Yuan", symbol="¥"),
    SupportedCurrency(code="CHF", name="Swiss Franc", symbol="CHF"),
    SupportedCurrency(code="SGD", name="Singapore Dollar", symbol="S$"),
]


@router.get("/currency", response_model=CurrencyConfig)
async def get_current_currency():
    """Get the current system currency configuration."""
    return current_currency


@router.put("/currency", response_model=CurrencyConfig)
async def update_currency(currency_data: CurrencyUpdateRequest):
    """Update the system currency configuration."""
    global current_currency
    
    # Check if currency is supported
    supported_codes = [c.code for c in SUPPORTED_CURRENCIES]
    if currency_data.currency_code not in supported_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Currency code '{currency_data.currency_code}' is not supported"
        )
    
    # Find the currency details
    currency_details = next(
        (c for c in SUPPORTED_CURRENCIES if c.code == currency_data.currency_code),
        None
    )
    
    if not currency_details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency not found"
        )
    
    # Update the currency configuration
    current_currency = CurrencyConfig(
        currency_code=currency_details.code,
        symbol=currency_details.symbol,
        description=currency_data.description or currency_details.name,
        is_default=True
    )
    
    return current_currency


@router.get("/currency/supported", response_model=List[SupportedCurrency])
async def get_supported_currencies():
    """Get list of supported currencies."""
    return SUPPORTED_CURRENCIES