from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from uuid import UUID

from app.modules.analytics.models import (
    ReportType, ReportStatus, ReportFormat, MetricType, 
    AlertSeverity, AlertStatus
)


# Analytics Report Schemas
class AnalyticsReportCreate(BaseModel):
    """Schema for creating a new analytics report."""
    report_name: str = Field(..., description="Name of the report")
    report_type: ReportType = Field(..., description="Type of report")
    report_format: ReportFormat = Field(..., description="Format of the report")
    start_date: Optional[datetime] = Field(None, description="Start date for report data")
    end_date: Optional[datetime] = Field(None, description="End date for report data")
    filters: Optional[Dict[str, Any]] = Field(None, description="JSON filters applied to the report")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional report parameters")
    
    @field_validator('report_name')
    @classmethod
    def validate_report_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Report name cannot be empty")
        if len(v) > 200:
            raise ValueError("Report name cannot exceed 200 characters")
        return v.strip()
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if v is not None and info.data.get('start_date') is not None:
            if v < info.data.get('start_date'):
                raise ValueError("End date must be after start date")
        return v


class AnalyticsReportUpdate(BaseModel):
    """Schema for updating an analytics report."""
    report_name: Optional[str] = Field(None, description="Name of the report")
    report_type: Optional[ReportType] = Field(None, description="Type of report")
    report_format: Optional[ReportFormat] = Field(None, description="Format of the report")
    start_date: Optional[datetime] = Field(None, description="Start date for report data")
    end_date: Optional[datetime] = Field(None, description="End date for report data")
    filters: Optional[Dict[str, Any]] = Field(None, description="JSON filters applied to the report")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional report parameters")
    
    @field_validator('report_name')
    @classmethod
    def validate_report_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Report name cannot be empty")
            if len(v) > 200:
                raise ValueError("Report name cannot exceed 200 characters")
        return v.strip() if v else None


class AnalyticsReportResponse(BaseModel):
    """Schema for analytics report response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    report_name: str
    report_type: ReportType
    report_format: ReportFormat
    report_status: ReportStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    filters: Optional[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]]
    file_path: Optional[str]
    file_size: Optional[str]
    generated_by: UUID
    generated_at: Optional[datetime]
    error_message: Optional[str]
    report_metadata: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.report_name} ({self.report_type.value})"
    
    @computed_field
    @property
    def is_completed(self) -> bool:
        return self.report_status == ReportStatus.COMPLETED
    
    @computed_field
    @property
    def is_failed(self) -> bool:
        return self.report_status == ReportStatus.FAILED
    
    @computed_field
    @property
    def file_size_mb(self) -> Optional[float]:
        if self.file_size:
            try:
                return float(self.file_size) / (1024 * 1024)
            except ValueError:
                return None
        return None
    
    @computed_field
    @property
    def duration_minutes(self) -> Optional[int]:
        if self.generated_at:
            return int((self.generated_at - self.created_at).total_seconds() / 60)
        return None


class AnalyticsReportListResponse(BaseModel):
    """Schema for analytics report list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    report_name: str
    report_type: ReportType
    report_format: ReportFormat
    report_status: ReportStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    file_size: Optional[str]
    generated_by: UUID
    generated_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.report_name} ({self.report_type.value})"
    
    @computed_field
    @property
    def is_completed(self) -> bool:
        return self.report_status == ReportStatus.COMPLETED


# Business Metric Schemas
class BusinessMetricCreate(BaseModel):
    """Schema for creating a new business metric."""
    metric_name: str = Field(..., description="Name of the metric")
    metric_type: MetricType = Field(..., description="Type of metric")
    category: str = Field(..., description="Category of the metric")
    current_value: Decimal = Field(..., description="Current value of the metric")
    previous_value: Optional[Decimal] = Field(None, description="Previous value of the metric")
    target_value: Optional[Decimal] = Field(None, description="Target value for the metric")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    calculation_method: Optional[str] = Field(None, description="How the metric is calculated")
    metric_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @field_validator('metric_name')
    @classmethod
    def validate_metric_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Metric name cannot be empty")
        if len(v) > 100:
            raise ValueError("Metric name cannot exceed 100 characters")
        return v.strip()
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if not v or not v.strip():
            raise ValueError("Category cannot be empty")
        if len(v) > 50:
            raise ValueError("Category cannot exceed 50 characters")
        return v.strip()
    
    @field_validator('unit')
    @classmethod
    def validate_unit(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError("Unit cannot exceed 20 characters")
        return v


class BusinessMetricUpdate(BaseModel):
    """Schema for updating a business metric."""
    metric_name: Optional[str] = Field(None, description="Name of the metric")
    metric_type: Optional[MetricType] = Field(None, description="Type of metric")
    category: Optional[str] = Field(None, description="Category of the metric")
    current_value: Optional[Decimal] = Field(None, description="Current value of the metric")
    previous_value: Optional[Decimal] = Field(None, description="Previous value of the metric")
    target_value: Optional[Decimal] = Field(None, description="Target value for the metric")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    calculation_method: Optional[str] = Field(None, description="How the metric is calculated")
    metric_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @field_validator('metric_name')
    @classmethod
    def validate_metric_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Metric name cannot be empty")
            if len(v) > 100:
                raise ValueError("Metric name cannot exceed 100 characters")
        return v.strip() if v else None


class BusinessMetricResponse(BaseModel):
    """Schema for business metric response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    metric_name: str
    metric_type: MetricType
    category: str
    current_value: Decimal
    previous_value: Optional[Decimal]
    target_value: Optional[Decimal]
    unit: Optional[str]
    calculation_method: Optional[str]
    tracked_date: datetime
    metric_metadata: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.metric_name} ({self.category})"
    
    @computed_field
    @property
    def formatted_value(self) -> str:
        if self.unit:
            return f"{self.current_value} {self.unit}"
        return str(self.current_value)
    
    @computed_field
    @property
    def change_percentage(self) -> Optional[Decimal]:
        if self.previous_value is None or self.previous_value == 0:
            return None
        
        change = ((self.current_value - self.previous_value) / self.previous_value) * 100
        return change.quantize(Decimal('0.01'))
    
    @computed_field
    @property
    def target_achievement(self) -> Optional[Decimal]:
        if self.target_value is None or self.target_value == 0:
            return None
        
        achievement = (self.current_value / self.target_value) * 100
        return achievement.quantize(Decimal('0.01'))
    
    @computed_field
    @property
    def is_target_met(self) -> bool:
        if self.target_value is None:
            return False
        return self.current_value >= self.target_value


class BusinessMetricListResponse(BaseModel):
    """Schema for business metric list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    metric_name: str
    metric_type: MetricType
    category: str
    current_value: Decimal
    target_value: Optional[Decimal]
    unit: Optional[str]
    tracked_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.metric_name} ({self.category})"
    
    @computed_field
    @property
    def formatted_value(self) -> str:
        if self.unit:
            return f"{self.current_value} {self.unit}"
        return str(self.current_value)


# System Alert Schemas
class SystemAlertCreate(BaseModel):
    """Schema for creating a new system alert."""
    alert_name: str = Field(..., description="Name of the alert")
    alert_type: str = Field(..., description="Type of alert")
    severity: AlertSeverity = Field(..., description="Severity level of the alert")
    message: str = Field(..., description="Alert message")
    description: Optional[str] = Field(None, description="Detailed description of the alert")
    source: Optional[str] = Field(None, description="Source of the alert")
    trigger_condition: Optional[str] = Field(None, description="Condition that triggered the alert")
    alert_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @field_validator('alert_name')
    @classmethod
    def validate_alert_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Alert name cannot be empty")
        if len(v) > 100:
            raise ValueError("Alert name cannot exceed 100 characters")
        return v.strip()
    
    @field_validator('alert_type')
    @classmethod
    def validate_alert_type(cls, v):
        if not v or not v.strip():
            raise ValueError("Alert type cannot be empty")
        if len(v) > 20:
            raise ValueError("Alert type cannot exceed 20 characters")
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Alert message cannot be empty")
        return v.strip()
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError("Source cannot exceed 100 characters")
        return v


class SystemAlertUpdate(BaseModel):
    """Schema for updating a system alert."""
    alert_name: Optional[str] = Field(None, description="Name of the alert")
    alert_type: Optional[str] = Field(None, description="Type of alert")
    severity: Optional[AlertSeverity] = Field(None, description="Severity level of the alert")
    message: Optional[str] = Field(None, description="Alert message")
    description: Optional[str] = Field(None, description="Detailed description of the alert")
    source: Optional[str] = Field(None, description="Source of the alert")
    trigger_condition: Optional[str] = Field(None, description="Condition that triggered the alert")
    alert_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SystemAlertResponse(BaseModel):
    """Schema for system alert response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    alert_name: str
    alert_type: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    description: Optional[str]
    source: Optional[str]
    trigger_condition: Optional[str]
    resolution_notes: Optional[str]
    acknowledged_by: Optional[UUID]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[UUID]
    resolved_at: Optional[datetime]
    alert_metadata: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.alert_name} ({self.severity.value})"
    
    @computed_field
    @property
    def is_resolved(self) -> bool:
        return self.status == AlertStatus.RESOLVED
    
    @computed_field
    @property
    def is_critical(self) -> bool:
        return self.severity == AlertSeverity.CRITICAL
    
    @computed_field
    @property
    def duration_minutes(self) -> int:
        if self.resolved_at:
            return int((self.resolved_at - self.created_at).total_seconds() / 60)
        return int((datetime.utcnow() - self.created_at).total_seconds() / 60)


class SystemAlertListResponse(BaseModel):
    """Schema for system alert list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    alert_name: str
    alert_type: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    source: Optional[str]
    acknowledged_by: Optional[UUID]
    resolved_by: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.alert_name} ({self.severity.value})"
    
    @computed_field
    @property
    def is_critical(self) -> bool:
        return self.severity == AlertSeverity.CRITICAL


# Action Schemas
class AlertAcknowledgeRequest(BaseModel):
    """Schema for acknowledging an alert."""
    notes: Optional[str] = Field(None, description="Acknowledgment notes")


class AlertResolveRequest(BaseModel):
    """Schema for resolving an alert."""
    resolution_notes: str = Field(..., description="Resolution notes")
    
    @field_validator('resolution_notes')
    @classmethod
    def validate_resolution_notes(cls, v):
        if not v or not v.strip():
            raise ValueError("Resolution notes cannot be empty")
        return v.strip()


class MetricValueUpdate(BaseModel):
    """Schema for updating metric value."""
    new_value: Decimal = Field(..., description="New metric value")


class ReportGenerationRequest(BaseModel):
    """Schema for generating a report."""
    start_date: Optional[datetime] = Field(None, description="Start date for report data")
    end_date: Optional[datetime] = Field(None, description="End date for report data")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")


# Dashboard Schemas
class AnalyticsDashboard(BaseModel):
    """Schema for analytics dashboard."""
    total_reports: int
    pending_reports: int
    completed_reports: int
    failed_reports: int
    active_alerts: int
    critical_alerts: int
    total_metrics: int
    metrics_with_targets: int
    metrics_meeting_targets: int
    recent_reports: List[AnalyticsReportListResponse]
    critical_alerts_list: List[SystemAlertListResponse]
    key_metrics: List[BusinessMetricListResponse]


class SystemHealthSummary(BaseModel):
    """Schema for system health summary."""
    overall_health: str
    active_alerts: int
    critical_alerts: int
    warning_alerts: int
    system_uptime: str
    last_backup: Optional[datetime]
    database_size: str
    storage_usage: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float


class AnalyticsSearch(BaseModel):
    """Schema for analytics search."""
    report_type: Optional[ReportType] = Field(None, description="Filter by report type")
    report_status: Optional[ReportStatus] = Field(None, description="Filter by report status")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    generated_by: Optional[UUID] = Field(None, description="Filter by generator")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if v is not None and info.data.get('start_date') is not None:
            if v < info.data.get('start_date'):
                raise ValueError("End date must be after start date")
        return v


class MetricSearch(BaseModel):
    """Schema for metric search."""
    metric_type: Optional[MetricType] = Field(None, description="Filter by metric type")
    category: Optional[str] = Field(None, description="Filter by category")
    has_target: Optional[bool] = Field(None, description="Filter by target presence")
    target_met: Optional[bool] = Field(None, description="Filter by target achievement")
    tracked_from: Optional[datetime] = Field(None, description="Filter by tracked date from")
    tracked_to: Optional[datetime] = Field(None, description="Filter by tracked date to")


class AlertSearch(BaseModel):
    """Schema for alert search."""
    alert_type: Optional[str] = Field(None, description="Filter by alert type")
    severity: Optional[AlertSeverity] = Field(None, description="Filter by severity")
    status: Optional[AlertStatus] = Field(None, description="Filter by status")
    source: Optional[str] = Field(None, description="Filter by source")
    created_from: Optional[datetime] = Field(None, description="Filter by created date from")
    created_to: Optional[datetime] = Field(None, description="Filter by created date to")
    resolved_from: Optional[datetime] = Field(None, description="Filter by resolved date from")
    resolved_to: Optional[datetime] = Field(None, description="Filter by resolved date to")