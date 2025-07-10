from typing import Any, Dict, List, Optional, Type, Union, Callable
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Select, and_, or_, not_, func
from sqlalchemy.orm import InstrumentedAttribute
import operator
from functools import reduce


class FilterOperator(str, Enum):
    """Supported filter operators."""
    EQ = "eq"           # Equal
    NEQ = "neq"         # Not equal
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    IN = "in"           # In list
    NOT_IN = "not_in"   # Not in list
    LIKE = "like"       # SQL LIKE
    ILIKE = "ilike"     # Case-insensitive LIKE
    CONTAINS = "contains"     # Contains substring
    ICONTAINS = "icontains"   # Case-insensitive contains
    STARTS = "starts"         # Starts with
    ISTARTS = "istarts"       # Case-insensitive starts with
    ENDS = "ends"             # Ends with
    IENDS = "iends"           # Case-insensitive ends with
    IS_NULL = "is_null"       # Is null
    IS_NOT_NULL = "is_not_null"  # Is not null
    BETWEEN = "between"       # Between two values


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class FilterCondition(BaseModel):
    """Single filter condition."""
    field: str = Field(description="Field name to filter on")
    operator: FilterOperator = Field(default=FilterOperator.EQ, description="Filter operator")
    value: Any = Field(description="Value to filter by")
    case_sensitive: bool = Field(default=True, description="Case sensitivity for string operations")


class FilterGroup(BaseModel):
    """Group of filter conditions with logical operator."""
    conditions: List[Union[FilterCondition, "FilterGroup"]] = Field(description="Filter conditions")
    logic: str = Field(default="AND", regex="^(AND|OR)$", description="Logical operator")


# Allow FilterGroup to reference itself
FilterGroup.model_rebuild()


class SortSpec(BaseModel):
    """Sort specification."""
    field: str = Field(description="Field name to sort by")
    order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")


class SearchSpec(BaseModel):
    """Search specification for full-text search."""
    query: str = Field(description="Search query")
    fields: List[str] = Field(description="Fields to search in")
    case_sensitive: bool = Field(default=False, description="Case sensitivity")


class DateRangeFilter(BaseModel):
    """Date range filter."""
    field: str = Field(description="Date field name")
    start_date: Optional[datetime] = Field(None, description="Start date (inclusive)")
    end_date: Optional[datetime] = Field(None, description="End date (inclusive)")


class NumericRangeFilter(BaseModel):
    """Numeric range filter."""
    field: str = Field(description="Numeric field name")
    min_value: Optional[float] = Field(None, description="Minimum value (inclusive)")
    max_value: Optional[float] = Field(None, description="Maximum value (inclusive)")


class FilterBuilder:
    """
    Build SQLAlchemy filters from filter specifications.
    
    Example:
        ```python
        # Simple filter
        filter_spec = FilterCondition(field="name", operator=FilterOperator.LIKE, value="%john%")
        query = FilterBuilder.apply_filter(query, User, filter_spec)
        
        # Complex filter group
        filter_group = FilterGroup(
            conditions=[
                FilterCondition(field="is_active", operator=FilterOperator.EQ, value=True),
                FilterCondition(field="created_at", operator=FilterOperator.GTE, value=datetime.now())
            ],
            logic="AND"
        )
        query = FilterBuilder.apply_filter_group(query, User, filter_group)
        ```
    """
    
    @staticmethod
    def get_field(model: Type, field_name: str) -> InstrumentedAttribute:
        """
        Get model field by name, supporting nested fields.
        
        Args:
            model: SQLAlchemy model class
            field_name: Field name (supports dot notation for relationships)
            
        Returns:
            Model field attribute
        """
        parts = field_name.split(".")
        current = model
        
        for part in parts:
            if hasattr(current, part):
                attr = getattr(current, part)
                if hasattr(attr, "property") and hasattr(attr.property, "mapper"):
                    # This is a relationship, get the related model
                    current = attr.property.mapper.class_
                else:
                    current = attr
            else:
                raise ValueError(f"Field '{part}' not found in {current}")
        
        return current
    
    @staticmethod
    def apply_operator(field: InstrumentedAttribute, op: FilterOperator, value: Any, case_sensitive: bool = True) -> Any:
        """
        Apply filter operator to field.
        
        Args:
            field: Model field
            op: Filter operator
            value: Filter value
            case_sensitive: Case sensitivity for string operations
            
        Returns:
            SQLAlchemy filter expression
        """
        if op == FilterOperator.EQ:
            return field == value
        elif op == FilterOperator.NEQ:
            return field != value
        elif op == FilterOperator.GT:
            return field > value
        elif op == FilterOperator.GTE:
            return field >= value
        elif op == FilterOperator.LT:
            return field < value
        elif op == FilterOperator.LTE:
            return field <= value
        elif op == FilterOperator.IN:
            return field.in_(value if isinstance(value, list) else [value])
        elif op == FilterOperator.NOT_IN:
            return ~field.in_(value if isinstance(value, list) else [value])
        elif op == FilterOperator.LIKE:
            return field.like(value) if case_sensitive else field.ilike(value)
        elif op == FilterOperator.ILIKE:
            return field.ilike(value)
        elif op == FilterOperator.CONTAINS:
            pattern = f"%{value}%"
            return field.like(pattern) if case_sensitive else field.ilike(pattern)
        elif op == FilterOperator.ICONTAINS:
            return field.ilike(f"%{value}%")
        elif op == FilterOperator.STARTS:
            pattern = f"{value}%"
            return field.like(pattern) if case_sensitive else field.ilike(pattern)
        elif op == FilterOperator.ISTARTS:
            return field.ilike(f"{value}%")
        elif op == FilterOperator.ENDS:
            pattern = f"%{value}"
            return field.like(pattern) if case_sensitive else field.ilike(pattern)
        elif op == FilterOperator.IENDS:
            return field.ilike(f"%{value}")
        elif op == FilterOperator.IS_NULL:
            return field.is_(None)
        elif op == FilterOperator.IS_NOT_NULL:
            return field.isnot(None)
        elif op == FilterOperator.BETWEEN:
            if isinstance(value, list) and len(value) == 2:
                return field.between(value[0], value[1])
            else:
                raise ValueError(f"BETWEEN operator requires a list of two values")
        else:
            raise ValueError(f"Unsupported operator: {op}")
    
    @staticmethod
    def apply_filter(query: Select, model: Type, filter_spec: FilterCondition) -> Select:
        """
        Apply a single filter condition to query.
        
        Args:
            query: SQLAlchemy query
            model: Model class
            filter_spec: Filter condition
            
        Returns:
            Modified query
        """
        field = FilterBuilder.get_field(model, filter_spec.field)
        condition = FilterBuilder.apply_operator(
            field, filter_spec.operator, filter_spec.value, filter_spec.case_sensitive
        )
        return query.where(condition)
    
    @staticmethod
    def apply_filter_group(query: Select, model: Type, filter_group: FilterGroup) -> Select:
        """
        Apply a group of filters to query.
        
        Args:
            query: SQLAlchemy query
            model: Model class
            filter_group: Filter group
            
        Returns:
            Modified query
        """
        conditions = []
        
        for item in filter_group.conditions:
            if isinstance(item, FilterCondition):
                field = FilterBuilder.get_field(model, item.field)
                condition = FilterBuilder.apply_operator(
                    field, item.operator, item.value, item.case_sensitive
                )
                conditions.append(condition)
            elif isinstance(item, FilterGroup):
                # Recursively handle nested groups
                sub_conditions = []
                for sub_item in item.conditions:
                    if isinstance(sub_item, FilterCondition):
                        field = FilterBuilder.get_field(model, sub_item.field)
                        condition = FilterBuilder.apply_operator(
                            field, sub_item.operator, sub_item.value, sub_item.case_sensitive
                        )
                        sub_conditions.append(condition)
                
                if sub_conditions:
                    if item.logic == "OR":
                        conditions.append(or_(*sub_conditions))
                    else:
                        conditions.append(and_(*sub_conditions))
        
        if conditions:
            if filter_group.logic == "OR":
                query = query.where(or_(*conditions))
            else:
                query = query.where(and_(*conditions))
        
        return query
    
    @staticmethod
    def apply_search(query: Select, model: Type, search_spec: SearchSpec) -> Select:
        """
        Apply search filter to multiple fields.
        
        Args:
            query: SQLAlchemy query
            model: Model class
            search_spec: Search specification
            
        Returns:
            Modified query
        """
        conditions = []
        search_pattern = f"%{search_spec.query}%"
        
        for field_name in search_spec.fields:
            try:
                field = FilterBuilder.get_field(model, field_name)
                if search_spec.case_sensitive:
                    conditions.append(field.like(search_pattern))
                else:
                    conditions.append(field.ilike(search_pattern))
            except ValueError:
                # Skip invalid fields
                continue
        
        if conditions:
            query = query.where(or_(*conditions))
        
        return query
    
    @staticmethod
    def apply_sort(query: Select, model: Type, sort_specs: List[SortSpec]) -> Select:
        """
        Apply sorting to query.
        
        Args:
            query: SQLAlchemy query
            model: Model class
            sort_specs: List of sort specifications
            
        Returns:
            Modified query
        """
        for sort_spec in sort_specs:
            field = FilterBuilder.get_field(model, sort_spec.field)
            if sort_spec.order == SortOrder.DESC:
                query = query.order_by(field.desc())
            else:
                query = query.order_by(field.asc())
        
        return query
    
    @staticmethod
    def apply_date_range(query: Select, model: Type, date_filter: DateRangeFilter) -> Select:
        """
        Apply date range filter.
        
        Args:
            query: SQLAlchemy query
            model: Model class
            date_filter: Date range filter
            
        Returns:
            Modified query
        """
        field = FilterBuilder.get_field(model, date_filter.field)
        
        if date_filter.start_date:
            query = query.where(field >= date_filter.start_date)
        
        if date_filter.end_date:
            query = query.where(field <= date_filter.end_date)
        
        return query
    
    @staticmethod
    def apply_numeric_range(query: Select, model: Type, numeric_filter: NumericRangeFilter) -> Select:
        """
        Apply numeric range filter.
        
        Args:
            query: SQLAlchemy query
            model: Model class
            numeric_filter: Numeric range filter
            
        Returns:
            Modified query
        """
        field = FilterBuilder.get_field(model, numeric_filter.field)
        
        if numeric_filter.min_value is not None:
            query = query.where(field >= numeric_filter.min_value)
        
        if numeric_filter.max_value is not None:
            query = query.where(field <= numeric_filter.max_value)
        
        return query


class DynamicFilter(BaseModel):
    """
    Dynamic filter specification supporting multiple filter types.
    
    Example:
        ```python
        filter_spec = DynamicFilter(
            filters=[
                FilterCondition(field="status", operator=FilterOperator.EQ, value="active"),
                FilterCondition(field="age", operator=FilterOperator.GTE, value=18)
            ],
            search=SearchSpec(query="john", fields=["name", "email"]),
            date_ranges=[
                DateRangeFilter(field="created_at", start_date=datetime(2023, 1, 1))
            ],
            sort=[
                SortSpec(field="created_at", order=SortOrder.DESC)
            ]
        )
        ```
    """
    filters: List[FilterCondition] = Field(default_factory=list, description="Filter conditions")
    filter_groups: List[FilterGroup] = Field(default_factory=list, description="Filter groups")
    search: Optional[SearchSpec] = Field(None, description="Search specification")
    date_ranges: List[DateRangeFilter] = Field(default_factory=list, description="Date range filters")
    numeric_ranges: List[NumericRangeFilter] = Field(default_factory=list, description="Numeric range filters")
    sort: List[SortSpec] = Field(default_factory=list, description="Sort specifications")
    
    def apply(self, query: Select, model: Type) -> Select:
        """
        Apply all filters to query.
        
        Args:
            query: SQLAlchemy query
            model: Model class
            
        Returns:
            Modified query
        """
        # Apply individual filters
        for filter_spec in self.filters:
            query = FilterBuilder.apply_filter(query, model, filter_spec)
        
        # Apply filter groups
        for filter_group in self.filter_groups:
            query = FilterBuilder.apply_filter_group(query, model, filter_group)
        
        # Apply search
        if self.search:
            query = FilterBuilder.apply_search(query, model, self.search)
        
        # Apply date ranges
        for date_filter in self.date_ranges:
            query = FilterBuilder.apply_date_range(query, model, date_filter)
        
        # Apply numeric ranges
        for numeric_filter in self.numeric_ranges:
            query = FilterBuilder.apply_numeric_range(query, model, numeric_filter)
        
        # Apply sorting
        if self.sort:
            query = FilterBuilder.apply_sort(query, model, self.sort)
        
        return query


def create_filter(**kwargs) -> FilterCondition:
    """
    Convenience function to create a filter condition.
    
    Example:
        ```python
        filter = create_filter(field="name", operator="like", value="%john%")
        ```
    """
    return FilterCondition(**kwargs)


def create_search(query: str, *fields: str, case_sensitive: bool = False) -> SearchSpec:
    """
    Convenience function to create a search specification.
    
    Example:
        ```python
        search = create_search("john", "name", "email", "username")
        ```
    """
    return SearchSpec(query=query, fields=list(fields), case_sensitive=case_sensitive)


def create_sort(*specs: tuple) -> List[SortSpec]:
    """
    Convenience function to create sort specifications.
    
    Example:
        ```python
        sort = create_sort(("created_at", "desc"), ("name", "asc"))
        ```
    """
    return [
        SortSpec(field=field, order=SortOrder(order))
        for field, order in specs
    ]


__all__ = [
    "FilterOperator",
    "SortOrder",
    "FilterCondition",
    "FilterGroup",
    "SortSpec",
    "SearchSpec",
    "DateRangeFilter",
    "NumericRangeFilter",
    "FilterBuilder",
    "DynamicFilter",
    "create_filter",
    "create_search",
    "create_sort",
]