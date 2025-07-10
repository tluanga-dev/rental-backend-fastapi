from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Boolean, String, Integer, event
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import sqlalchemy as sa


# Create a UUID type that works with SQLite
class UUIDType(sa.TypeDecorator):
    """
    SQLite-compatible UUID type.
    Uses CHAR(36), storing as stringified hex values.
    """
    impl = sa.CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(sa.CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, UUID):
                return UUID(value)
            else:
                return value


# Base class for all models
@as_declarative()
class Base:
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    created_by: Optional[str]
    updated_by: Optional[str]
    
    __name__: str
    
    # Generate table name from class name
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.
        Converts CamelCase to snake_case and pluralizes.
        """
        import re
        # Convert CamelCase to snake_case
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
        # Simple pluralization (can be overridden in model if needed)
        if name.endswith('y'):
            return f"{name[:-1]}ies"
        elif name.endswith('s'):
            return f"{name}es"
        else:
            return f"{name}s"


class TimestampMixin:
    """Mixin for timestamp fields."""
    
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
            comment="Record creation timestamp"
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
            comment="Record last update timestamp"
        )


class AuditMixin:
    """Mixin for audit fields."""
    
    @declared_attr
    def created_by(cls):
        return Column(
            String(255),
            nullable=True,
            comment="User who created the record"
        )
    
    @declared_attr
    def updated_by(cls):
        return Column(
            String(255),
            nullable=True,
            comment="User who last updated the record"
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    @declared_attr
    def is_active(cls):
        return Column(
            Boolean,
            default=True,
            nullable=False,
            index=True,
            comment="Soft delete flag"
        )
    
    @declared_attr
    def deleted_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=True,
            comment="Soft delete timestamp"
        )
    
    @declared_attr
    def deleted_by(cls):
        return Column(
            String(255),
            nullable=True,
            comment="User who deleted the record"
        )
    
    def soft_delete(self, deleted_by: Optional[str] = None):
        """Soft delete the record."""
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
    
    def restore(self):
        """Restore a soft deleted record."""
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None


class BaseModel(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """
    Base model class with common fields and functionality.
    All models should inherit from this class.
    """
    __abstract__ = True
    
    id = Column(
        UUIDType(),
        primary_key=True,
        default=uuid4,
        comment="Primary key"
    )
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs):
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def create(cls, **kwargs):
        """Create a new instance."""
        instance = cls()
        instance.update(**kwargs)
        return instance
    
    def __repr__(self):
        """String representation of model."""
        attrs = []
        for column in self.__table__.columns:
            attrs.append(f"{column.name}={getattr(self, column.name)}")
        return f"<{self.__class__.__name__}({', '.join(attrs[:3])}, ...)>"


class IntegerIDMixin:
    """Mixin for models that use integer IDs instead of UUIDs."""
    
    @declared_attr
    def id(cls):
        return Column(
            Integer,
            primary_key=True,
            autoincrement=True,
            comment="Primary key"
        )


class NamedModelMixin:
    """Mixin for models with name field."""
    
    @declared_attr
    def name(cls):
        return Column(
            String(255),
            nullable=False,
            index=True,
            comment="Name"
        )
    
    @declared_attr
    def description(cls):
        return Column(
            String(1000),
            nullable=True,
            comment="Description"
        )


class CodedModelMixin:
    """Mixin for models with unique code field."""
    
    @declared_attr
    def code(cls):
        return Column(
            String(50),
            nullable=False,
            unique=True,
            index=True,
            comment="Unique code"
        )


class OrderedModelMixin:
    """Mixin for models that need ordering."""
    
    @declared_attr
    def display_order(cls):
        return Column(
            Integer,
            nullable=False,
            default=0,
            comment="Display order"
        )
    
    @declared_attr
    def is_default(cls):
        return Column(
            Boolean,
            nullable=False,
            default=False,
            comment="Default flag"
        )


# Event listeners for automatic timestamp updates
@event.listens_for(BaseModel, 'before_insert', propagate=True)
def receive_before_insert(mapper, connection, target):
    """Set created_at before insert."""
    if hasattr(target, 'created_at') and target.created_at is None:
        target.created_at = datetime.utcnow()
    if hasattr(target, 'updated_at') and target.updated_at is None:
        target.updated_at = datetime.utcnow()


@event.listens_for(BaseModel, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """Update updated_at before update."""
    if hasattr(target, 'updated_at'):
        target.updated_at = datetime.utcnow()


# Export metadata for migrations
metadata = Base.metadata

__all__ = [
    "Base",
    "BaseModel",
    "UUIDType",
    "TimestampMixin",
    "AuditMixin",
    "SoftDeleteMixin",
    "IntegerIDMixin",
    "NamedModelMixin",
    "CodedModelMixin",
    "OrderedModelMixin",
    "metadata",
]