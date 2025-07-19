"""
Rental Returns Models

Models specific to rental return operations, inspections, and lifecycle tracking.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime

from app.db.base import BaseModel, UUIDType

# Import models from base models to avoid duplication
from app.modules.transactions.base.models import RentalInspection, RentalReturnEvent