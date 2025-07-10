from typing import List, Optional, Union, Tuple
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from datetime import datetime, date, timedelta
from enum import Enum
import math

from app.core.config import settings


class RoundingMethod(str, Enum):
    """Rounding methods for calculations."""
    HALF_UP = "half_up"
    HALF_DOWN = "half_down"
    UP = "up"
    DOWN = "down"
    HALF_EVEN = "half_even"


# Financial calculations
def calculate_percentage(
    value: Union[int, float, Decimal],
    percentage: Union[int, float, Decimal],
    decimal_places: int = 2
) -> Decimal:
    """
    Calculate percentage of a value.
    
    Args:
        value: Base value
        percentage: Percentage (0-100)
        decimal_places: Decimal places for result
        
    Returns:
        Calculated percentage amount
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    if not isinstance(percentage, Decimal):
        percentage = Decimal(str(percentage))
    
    result = value * (percentage / Decimal("100"))
    return result.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)


def calculate_tax(
    amount: Union[int, float, Decimal],
    tax_rate: Union[int, float, Decimal],
    inclusive: bool = False,
    decimal_places: int = 2
) -> Tuple[Decimal, Decimal]:
    """
    Calculate tax amount.
    
    Args:
        amount: Base amount
        tax_rate: Tax rate as percentage (0-100)
        inclusive: Whether tax is included in amount
        decimal_places: Decimal places for result
        
    Returns:
        Tuple of (tax_amount, net_amount)
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    if not isinstance(tax_rate, Decimal):
        tax_rate = Decimal(str(tax_rate))
    
    if inclusive:
        # Tax is included in amount
        # net = amount / (1 + tax_rate/100)
        net_amount = amount / (Decimal("1") + tax_rate / Decimal("100"))
        tax_amount = amount - net_amount
    else:
        # Tax is added to amount
        tax_amount = calculate_percentage(amount, tax_rate, decimal_places)
        net_amount = amount
    
    return (
        tax_amount.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP),
        net_amount.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)
    )


def calculate_discount(
    original_price: Union[int, float, Decimal],
    discount_percentage: Optional[Union[int, float, Decimal]] = None,
    discount_amount: Optional[Union[int, float, Decimal]] = None,
    decimal_places: int = 2
) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculate discounted price.
    
    Args:
        original_price: Original price
        discount_percentage: Discount as percentage
        discount_amount: Discount as fixed amount
        decimal_places: Decimal places for result
        
    Returns:
        Tuple of (discounted_price, discount_amount, effective_percentage)
    """
    if not isinstance(original_price, Decimal):
        original_price = Decimal(str(original_price))
    
    if discount_percentage is not None:
        if not isinstance(discount_percentage, Decimal):
            discount_percentage = Decimal(str(discount_percentage))
        
        discount_amt = calculate_percentage(original_price, discount_percentage, decimal_places)
        effective_pct = discount_percentage
    
    elif discount_amount is not None:
        if not isinstance(discount_amount, Decimal):
            discount_amount = Decimal(str(discount_amount))
        
        discount_amt = min(discount_amount, original_price)  # Can't discount more than price
        effective_pct = (discount_amt / original_price * Decimal("100")) if original_price > 0 else Decimal("0")
    
    else:
        discount_amt = Decimal("0")
        effective_pct = Decimal("0")
    
    discounted_price = original_price - discount_amt
    
    return (
        discounted_price.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP),
        discount_amt.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP),
        effective_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )


def calculate_compound_interest(
    principal: Union[int, float, Decimal],
    rate: Union[int, float, Decimal],
    time_periods: int,
    compounds_per_period: int = 1,
    decimal_places: int = 2
) -> Decimal:
    """
    Calculate compound interest.
    
    Args:
        principal: Principal amount
        rate: Interest rate per period as percentage
        time_periods: Number of time periods
        compounds_per_period: Compounding frequency per period
        decimal_places: Decimal places for result
        
    Returns:
        Final amount after compound interest
    """
    if not isinstance(principal, Decimal):
        principal = Decimal(str(principal))
    if not isinstance(rate, Decimal):
        rate = Decimal(str(rate))
    
    # A = P(1 + r/n)^(nt)
    rate_decimal = rate / Decimal("100")
    base = Decimal("1") + (rate_decimal / Decimal(str(compounds_per_period)))
    exponent = compounds_per_period * time_periods
    
    # Use float for power calculation, then convert back
    result = principal * Decimal(str(float(base) ** exponent))
    
    return result.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)


# Date and time calculations
def calculate_days_between(
    start_date: Union[datetime, date],
    end_date: Union[datetime, date],
    inclusive: bool = True
) -> int:
    """
    Calculate days between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        inclusive: Whether to include both start and end dates
        
    Returns:
        Number of days
    """
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    days = (end_date - start_date).days
    
    if inclusive:
        days += 1
    
    return max(0, days)


def calculate_business_days(
    start_date: Union[datetime, date],
    end_date: Union[datetime, date],
    holidays: Optional[List[date]] = None,
    weekend_days: Tuple[int, int] = (5, 6)  # Saturday, Sunday
) -> int:
    """
    Calculate business days between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        holidays: List of holiday dates
        weekend_days: Tuple of weekend day numbers (0=Monday, 6=Sunday)
        
    Returns:
        Number of business days
    """
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    holidays = holidays or []
    business_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() not in weekend_days and current_date not in holidays:
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days


def calculate_age(
    birth_date: Union[datetime, date],
    reference_date: Optional[Union[datetime, date]] = None
) -> int:
    """
    Calculate age in years.
    
    Args:
        birth_date: Birth date
        reference_date: Reference date (defaults to today)
        
    Returns:
        Age in years
    """
    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()
    
    if reference_date is None:
        reference_date = date.today()
    elif isinstance(reference_date, datetime):
        reference_date = reference_date.date()
    
    age = reference_date.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return max(0, age)


# Rental calculations
def calculate_rental_price(
    base_price: Union[int, float, Decimal],
    rental_days: int,
    pricing_method: str = "daily",
    weekly_discount: Optional[Union[int, float, Decimal]] = None,
    monthly_discount: Optional[Union[int, float, Decimal]] = None,
    decimal_places: int = 2
) -> Tuple[Decimal, Decimal]:
    """
    Calculate rental price based on duration.
    
    Args:
        base_price: Base daily price
        rental_days: Number of rental days
        pricing_method: Pricing method ("daily", "weekly", "monthly")
        weekly_discount: Discount percentage for weekly rentals
        monthly_discount: Discount percentage for monthly rentals
        decimal_places: Decimal places for result
        
    Returns:
        Tuple of (total_price, effective_daily_rate)
    """
    if not isinstance(base_price, Decimal):
        base_price = Decimal(str(base_price))
    
    if pricing_method == "weekly" and rental_days >= 7:
        weeks = rental_days // 7
        extra_days = rental_days % 7
        
        weekly_price = base_price * Decimal("7")
        if weekly_discount:
            weekly_price = calculate_discount(weekly_price, weekly_discount)[0]
        
        total_price = (weekly_price * Decimal(str(weeks))) + (base_price * Decimal(str(extra_days)))
    
    elif pricing_method == "monthly" and rental_days >= 30:
        months = rental_days // 30
        extra_days = rental_days % 30
        
        monthly_price = base_price * Decimal("30")
        if monthly_discount:
            monthly_price = calculate_discount(monthly_price, monthly_discount)[0]
        
        total_price = (monthly_price * Decimal(str(months))) + (base_price * Decimal(str(extra_days)))
    
    else:
        # Daily pricing
        total_price = base_price * Decimal(str(rental_days))
    
    effective_daily_rate = total_price / Decimal(str(rental_days)) if rental_days > 0 else base_price
    
    return (
        total_price.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP),
        effective_daily_rate.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)
    )


def calculate_late_fee(
    rental_amount: Union[int, float, Decimal],
    days_late: int,
    late_fee_rate: Optional[Union[int, float, Decimal]] = None,
    daily_fee: Optional[Union[int, float, Decimal]] = None,
    max_fee: Optional[Union[int, float, Decimal]] = None,
    decimal_places: int = 2
) -> Decimal:
    """
    Calculate late fee for rental.
    
    Args:
        rental_amount: Original rental amount
        days_late: Number of days late
        late_fee_rate: Late fee as percentage of rental per day
        daily_fee: Fixed daily late fee
        max_fee: Maximum late fee cap
        decimal_places: Decimal places for result
        
    Returns:
        Total late fee
    """
    if not isinstance(rental_amount, Decimal):
        rental_amount = Decimal(str(rental_amount))
    
    if days_late <= 0:
        return Decimal("0")
    
    if daily_fee is not None:
        # Fixed daily fee
        if not isinstance(daily_fee, Decimal):
            daily_fee = Decimal(str(daily_fee))
        total_fee = daily_fee * Decimal(str(days_late))
    
    elif late_fee_rate is not None:
        # Percentage-based fee
        if not isinstance(late_fee_rate, Decimal):
            late_fee_rate = Decimal(str(late_fee_rate))
        
        daily_fee_amount = calculate_percentage(rental_amount, late_fee_rate, decimal_places)
        total_fee = daily_fee_amount * Decimal(str(days_late))
    
    else:
        # Use default rate from settings
        late_fee_rate = Decimal(str(settings.DEFAULT_LATE_FEE_RATE * 100))
        daily_fee_amount = calculate_percentage(rental_amount, late_fee_rate, decimal_places)
        total_fee = daily_fee_amount * Decimal(str(days_late))
    
    # Apply maximum cap if specified
    if max_fee is not None:
        if not isinstance(max_fee, Decimal):
            max_fee = Decimal(str(max_fee))
        total_fee = min(total_fee, max_fee)
    
    return total_fee.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)


# Inventory calculations
def calculate_reorder_point(
    average_daily_usage: Union[int, float, Decimal],
    lead_time_days: int,
    safety_stock: Optional[Union[int, float, Decimal]] = None,
    safety_factor: Optional[float] = None
) -> int:
    """
    Calculate reorder point for inventory.
    
    Args:
        average_daily_usage: Average daily usage rate
        lead_time_days: Lead time in days
        safety_stock: Fixed safety stock quantity
        safety_factor: Safety factor multiplier (e.g., 1.5 for 50% buffer)
        
    Returns:
        Reorder point quantity
    """
    if not isinstance(average_daily_usage, Decimal):
        average_daily_usage = Decimal(str(average_daily_usage))
    
    base_reorder = average_daily_usage * Decimal(str(lead_time_days))
    
    if safety_stock is not None:
        if not isinstance(safety_stock, Decimal):
            safety_stock = Decimal(str(safety_stock))
        total = base_reorder + safety_stock
    elif safety_factor is not None:
        total = base_reorder * Decimal(str(safety_factor))
    else:
        total = base_reorder
    
    # Round up to nearest integer
    return int(math.ceil(float(total)))


def calculate_inventory_value(
    items: List[Tuple[Union[int, float], Union[int, float, Decimal]]],
    method: str = "average",
    decimal_places: int = 2
) -> Decimal:
    """
    Calculate inventory value.
    
    Args:
        items: List of (quantity, unit_cost) tuples
        method: Valuation method ("average", "fifo", "lifo")
        decimal_places: Decimal places for result
        
    Returns:
        Total inventory value
    """
    if not items:
        return Decimal("0")
    
    if method == "average":
        total_quantity = Decimal("0")
        total_value = Decimal("0")
        
        for quantity, unit_cost in items:
            qty = Decimal(str(quantity))
            cost = Decimal(str(unit_cost))
            total_quantity += qty
            total_value += qty * cost
        
        if total_quantity > 0:
            average_cost = total_value / total_quantity
            return total_value.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)
        else:
            return Decimal("0")
    
    else:  # FIFO/LIFO - simplified implementation
        total_value = Decimal("0")
        
        for quantity, unit_cost in items:
            qty = Decimal(str(quantity))
            cost = Decimal(str(unit_cost))
            total_value += qty * cost
        
        return total_value.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)


# Statistical calculations
def calculate_average(
    values: List[Union[int, float, Decimal]],
    decimal_places: int = 2
) -> Decimal:
    """
    Calculate average of values.
    
    Args:
        values: List of values
        decimal_places: Decimal places for result
        
    Returns:
        Average value
    """
    if not values:
        return Decimal("0")
    
    total = sum(Decimal(str(v)) for v in values)
    count = len(values)
    
    average = total / Decimal(str(count))
    return average.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)


def calculate_weighted_average(
    values_weights: List[Tuple[Union[int, float, Decimal], Union[int, float, Decimal]]],
    decimal_places: int = 2
) -> Decimal:
    """
    Calculate weighted average.
    
    Args:
        values_weights: List of (value, weight) tuples
        decimal_places: Decimal places for result
        
    Returns:
        Weighted average
    """
    if not values_weights:
        return Decimal("0")
    
    weighted_sum = Decimal("0")
    total_weight = Decimal("0")
    
    for value, weight in values_weights:
        val = Decimal(str(value))
        wgt = Decimal(str(weight))
        weighted_sum += val * wgt
        total_weight += wgt
    
    if total_weight > 0:
        average = weighted_sum / total_weight
        return average.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)
    else:
        return Decimal("0")


# Utility functions
def round_decimal(
    value: Union[int, float, Decimal],
    decimal_places: int = 2,
    method: RoundingMethod = RoundingMethod.HALF_UP
) -> Decimal:
    """
    Round decimal value using specified method.
    
    Args:
        value: Value to round
        decimal_places: Decimal places
        method: Rounding method
        
    Returns:
        Rounded value
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    quantizer = Decimal(f"0.{'0' * decimal_places}")
    
    if method == RoundingMethod.HALF_UP:
        return value.quantize(quantizer, rounding=ROUND_HALF_UP)
    elif method == RoundingMethod.DOWN:
        return value.quantize(quantizer, rounding=ROUND_DOWN)
    else:
        # Add other rounding methods as needed
        return value.quantize(quantizer, rounding=ROUND_HALF_UP)


def distribute_amount(
    total: Union[int, float, Decimal],
    num_parts: int,
    decimal_places: int = 2
) -> List[Decimal]:
    """
    Distribute amount evenly across parts, handling rounding.
    
    Args:
        total: Total amount to distribute
        num_parts: Number of parts
        decimal_places: Decimal places
        
    Returns:
        List of distributed amounts
    """
    if num_parts <= 0:
        return []
    
    if not isinstance(total, Decimal):
        total = Decimal(str(total))
    
    # Calculate base amount per part
    base_amount = total / Decimal(str(num_parts))
    base_rounded = base_amount.quantize(
        Decimal(f"0.{'0' * decimal_places}"),
        rounding=ROUND_DOWN
    )
    
    # Calculate remainder to distribute
    distributed_total = base_rounded * Decimal(str(num_parts))
    remainder = total - distributed_total
    
    # Create result list
    result = [base_rounded] * num_parts
    
    # Distribute remainder penny by penny
    penny = Decimal(f"0.{'0' * (decimal_places - 1)}1")
    remainder_pennies = int(remainder / penny)
    
    for i in range(min(remainder_pennies, num_parts)):
        result[i] += penny
    
    return result


__all__ = [
    "RoundingMethod",
    "calculate_percentage",
    "calculate_tax",
    "calculate_discount",
    "calculate_compound_interest",
    "calculate_days_between",
    "calculate_business_days",
    "calculate_age",
    "calculate_rental_price",
    "calculate_late_fee",
    "calculate_reorder_point",
    "calculate_inventory_value",
    "calculate_average",
    "calculate_weighted_average",
    "round_decimal",
    "distribute_amount",
]