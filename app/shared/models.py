from pydantic import BaseModel
from typing import Optional, List, Generic, TypeVar
from datetime import datetime

# Generic type for paginated responses
DataType = TypeVar('DataType')


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    
    model_config = {"from_attributes": True}


class PaginatedResponse(BaseResponse, Generic[DataType]):
    """Paginated response model"""
    data: List[DataType]
    page: int
    size: int
    total: int
    pages: int
    
    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error_type: str
    detail: str
    timestamp: datetime
    
    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    timestamp: datetime
    version: str
    
    model_config = {"from_attributes": True}