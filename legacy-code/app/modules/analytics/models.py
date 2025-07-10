from enum import Enum
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base import BaseModel, UUIDType


class ReportType(str, Enum):
    """Report type enumeration."""
    SALES = "SALES"
    RENTALS = "RENTALS"
    INVENTORY = "INVENTORY"
    CUSTOMER = "CUSTOMER"
    SUPPLIER = "SUPPLIER"
    FINANCIAL = "FINANCIAL"
    PERFORMANCE = "PERFORMANCE"
    SYSTEM = "SYSTEM"


class ReportStatus(str, Enum):
    """Report status enumeration."""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ReportFormat(str, Enum):
    """Report format enumeration."""
    PDF = "PDF"
    EXCEL = "EXCEL"
    CSV = "CSV"
    JSON = "JSON"


class MetricType(str, Enum):
    """Metric type enumeration."""
    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"
    PERCENTAGE = "PERCENTAGE"
    CURRENCY = "CURRENCY"


class AlertSeverity(str, Enum):
    """Alert severity enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Alert status enumeration."""
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    SUPPRESSED = "SUPPRESSED"


class AnalyticsReport(BaseModel):
    """
    Analytics report model for generating and storing business reports.
    
    Attributes:
        report_name: Name of the report
        report_type: Type of report (SALES, RENTALS, etc.)
        report_format: Format of the report (PDF, EXCEL, CSV, JSON)
        report_status: Current status of the report
        start_date: Start date for report data
        end_date: End date for report data
        filters: JSON filters applied to the report
        parameters: Additional report parameters
        file_path: Path to the generated report file
        file_size: Size of the generated report file in bytes
        generated_by: User who generated the report
        generated_at: When the report was generated
        error_message: Error message if report generation failed
        report_metadata: Additional metadata about the report
    """
    
    __tablename__ = "analytics_reports"
    
    report_name = Column(String(200), nullable=False, comment="Name of the report")
    report_type = Column(String(20), nullable=False, comment="Type of report")
    report_format = Column(String(10), nullable=False, comment="Format of the report")
    report_status = Column(String(20), nullable=False, default=ReportStatus.PENDING.value, comment="Current status")
    start_date = Column(DateTime, nullable=True, comment="Start date for report data")
    end_date = Column(DateTime, nullable=True, comment="End date for report data")
    filters = Column(JSON, nullable=True, comment="JSON filters applied to the report")
    parameters = Column(JSON, nullable=True, comment="Additional report parameters")
    file_path = Column(String(500), nullable=True, comment="Path to the generated report file")
    file_size = Column(String(20), nullable=True, comment="Size of the generated report file")
    generated_by = Column(UUIDType(), nullable=False, comment="User who generated the report")  # ForeignKey("users.id") - temporarily disabled
    generated_at = Column(DateTime, nullable=True, comment="When the report was generated")
    error_message = Column(Text, nullable=True, comment="Error message if generation failed")
    report_metadata = Column(JSON, nullable=True, comment="Additional metadata about the report")
    
    # Relationships
    generated_by_user = relationship("User", back_populates="generated_reports", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_analytics_report_type', 'report_type'),
        Index('idx_analytics_report_status', 'report_status'),
        Index('idx_analytics_report_generated_by', 'generated_by'),
        Index('idx_analytics_report_generated_at', 'generated_at'),
        Index('idx_analytics_report_date_range', 'start_date', 'end_date'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        report_name: str,
        report_type: ReportType,
        report_format: ReportFormat,
        generated_by: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize an Analytics Report.
        
        Args:
            report_name: Name of the report
            report_type: Type of report
            report_format: Format of the report
            generated_by: User who generated the report
            start_date: Start date for report data
            end_date: End date for report data
            filters: JSON filters applied to the report
            parameters: Additional report parameters
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.report_name = report_name
        self.report_type = report_type.value if isinstance(report_type, ReportType) else report_type
        self.report_format = report_format.value if isinstance(report_format, ReportFormat) else report_format
        self.generated_by = generated_by
        self.start_date = start_date
        self.end_date = end_date
        self.filters = filters or {}
        self.parameters = parameters or {}
        self.report_status = ReportStatus.PENDING.value
        self._validate()
    
    def _validate(self):
        """Validate analytics report business rules."""
        if not self.report_name or not self.report_name.strip():
            raise ValueError("Report name cannot be empty")
        
        if len(self.report_name) > 200:
            raise ValueError("Report name cannot exceed 200 characters")
        
        if self.report_type not in [rt.value for rt in ReportType]:
            raise ValueError(f"Invalid report type: {self.report_type}")
        
        if self.report_format not in [rf.value for rf in ReportFormat]:
            raise ValueError(f"Invalid report format: {self.report_format}")
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")
    
    def start_generation(self):
        """Start report generation."""
        self.report_status = ReportStatus.GENERATING.value
        self.generated_at = datetime.utcnow()
    
    def complete_generation(self, file_path: str, file_size: int):
        """Complete report generation."""
        self.report_status = ReportStatus.COMPLETED.value
        self.file_path = file_path
        self.file_size = str(file_size)
        self.error_message = None
    
    def fail_generation(self, error_message: str):
        """Fail report generation."""
        self.report_status = ReportStatus.FAILED.value
        self.error_message = error_message
    
    def cancel_generation(self):
        """Cancel report generation."""
        self.report_status = ReportStatus.CANCELLED.value
    
    def is_completed(self) -> bool:
        """Check if report generation is completed."""
        return self.report_status == ReportStatus.COMPLETED.value
    
    def is_failed(self) -> bool:
        """Check if report generation failed."""
        return self.report_status == ReportStatus.FAILED.value
    
    @property
    def display_name(self) -> str:
        """Get report display name."""
        return f"{self.report_name} ({self.report_type})"
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Get file size in MB."""
        if self.file_size:
            try:
                return float(self.file_size) / (1024 * 1024)
            except ValueError:
                return None
        return None
    
    def __str__(self) -> str:
        """String representation of analytics report."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of analytics report."""
        return (
            f"AnalyticsReport(id={self.id}, name='{self.report_name}', "
            f"type='{self.report_type}', status='{self.report_status}', "
            f"active={self.is_active})"
        )


class BusinessMetric(BaseModel):
    """
    Business metric model for tracking key performance indicators.
    
    Attributes:
        metric_name: Name of the metric
        metric_type: Type of metric (COUNTER, GAUGE, etc.)
        category: Category of the metric
        current_value: Current value of the metric
        previous_value: Previous value of the metric
        target_value: Target value for the metric
        unit: Unit of measurement
        calculation_method: How the metric is calculated
        tracked_date: Date when the metric was tracked
        metric_metadata: Additional metadata about the metric
    """
    
    __tablename__ = "business_metrics"
    
    metric_name = Column(String(100), nullable=False, comment="Name of the metric")
    metric_type = Column(String(20), nullable=False, comment="Type of metric")
    category = Column(String(50), nullable=False, comment="Category of the metric")
    current_value = Column(Numeric(15, 4), nullable=False, comment="Current value of the metric")
    previous_value = Column(Numeric(15, 4), nullable=True, comment="Previous value of the metric")
    target_value = Column(Numeric(15, 4), nullable=True, comment="Target value for the metric")
    unit = Column(String(20), nullable=True, comment="Unit of measurement")
    calculation_method = Column(Text, nullable=True, comment="How the metric is calculated")
    tracked_date = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Date when tracked")
    metric_metadata = Column(JSON, nullable=True, comment="Additional metadata about the metric")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_business_metric_name', 'metric_name'),
        Index('idx_business_metric_type', 'metric_type'),
        Index('idx_business_metric_category', 'category'),
        Index('idx_business_metric_tracked_date', 'tracked_date'),
        Index('idx_business_metric_name_date', 'metric_name', 'tracked_date'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        metric_name: str,
        metric_type: MetricType,
        category: str,
        current_value: Decimal,
        previous_value: Optional[Decimal] = None,
        target_value: Optional[Decimal] = None,
        unit: Optional[str] = None,
        calculation_method: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Business Metric.
        
        Args:
            metric_name: Name of the metric
            metric_type: Type of metric
            category: Category of the metric
            current_value: Current value of the metric
            previous_value: Previous value of the metric
            target_value: Target value for the metric
            unit: Unit of measurement
            calculation_method: How the metric is calculated
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.metric_name = metric_name
        self.metric_type = metric_type.value if isinstance(metric_type, MetricType) else metric_type
        self.category = category
        self.current_value = current_value
        self.previous_value = previous_value
        self.target_value = target_value
        self.unit = unit
        self.calculation_method = calculation_method
        self.tracked_date = datetime.utcnow()
        self._validate()
    
    def _validate(self):
        """Validate business metric business rules."""
        if not self.metric_name or not self.metric_name.strip():
            raise ValueError("Metric name cannot be empty")
        
        if len(self.metric_name) > 100:
            raise ValueError("Metric name cannot exceed 100 characters")
        
        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty")
        
        if len(self.category) > 50:
            raise ValueError("Category cannot exceed 50 characters")
        
        if self.metric_type not in [mt.value for mt in MetricType]:
            raise ValueError(f"Invalid metric type: {self.metric_type}")
        
        if self.unit and len(self.unit) > 20:
            raise ValueError("Unit cannot exceed 20 characters")
    
    def update_value(self, new_value: Decimal):
        """Update metric value."""
        self.previous_value = self.current_value
        self.current_value = new_value
        self.tracked_date = datetime.utcnow()
    
    def get_change_percentage(self) -> Optional[Decimal]:
        """Get percentage change from previous value."""
        if self.previous_value is None or self.previous_value == 0:
            return None
        
        change = ((self.current_value - self.previous_value) / self.previous_value) * 100
        return change.quantize(Decimal('0.01'))
    
    def get_target_achievement(self) -> Optional[Decimal]:
        """Get target achievement percentage."""
        if self.target_value is None or self.target_value == 0:
            return None
        
        achievement = (self.current_value / self.target_value) * 100
        return achievement.quantize(Decimal('0.01'))
    
    def is_target_met(self) -> bool:
        """Check if target is met."""
        if self.target_value is None:
            return False
        return self.current_value >= self.target_value
    
    @property
    def display_name(self) -> str:
        """Get metric display name."""
        return f"{self.metric_name} ({self.category})"
    
    @property
    def formatted_value(self) -> str:
        """Get formatted current value."""
        if self.unit:
            return f"{self.current_value} {self.unit}"
        return str(self.current_value)
    
    def __str__(self) -> str:
        """String representation of business metric."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of business metric."""
        return (
            f"BusinessMetric(id={self.id}, name='{self.metric_name}', "
            f"type='{self.metric_type}', value={self.current_value}, "
            f"active={self.is_active})"
        )


class SystemAlert(BaseModel):
    """
    System alert model for monitoring and alerting.
    
    Attributes:
        alert_name: Name of the alert
        alert_type: Type of alert (SYSTEM, BUSINESS, PERFORMANCE)
        severity: Severity level of the alert
        status: Current status of the alert
        message: Alert message
        description: Detailed description of the alert
        source: Source of the alert
        trigger_condition: Condition that triggered the alert
        resolution_notes: Notes on how the alert was resolved
        acknowledged_by: User who acknowledged the alert
        acknowledged_at: When the alert was acknowledged
        resolved_by: User who resolved the alert
        resolved_at: When the alert was resolved
        alert_metadata: Additional metadata about the alert
    """
    
    __tablename__ = "system_alerts"
    
    alert_name = Column(String(100), nullable=False, comment="Name of the alert")
    alert_type = Column(String(20), nullable=False, comment="Type of alert")
    severity = Column(String(20), nullable=False, comment="Severity level of the alert")
    status = Column(String(20), nullable=False, default=AlertStatus.ACTIVE.value, comment="Current status")
    message = Column(Text, nullable=False, comment="Alert message")
    description = Column(Text, nullable=True, comment="Detailed description of the alert")
    source = Column(String(100), nullable=True, comment="Source of the alert")
    trigger_condition = Column(Text, nullable=True, comment="Condition that triggered the alert")
    resolution_notes = Column(Text, nullable=True, comment="Notes on how the alert was resolved")
    acknowledged_by = Column(UUIDType(), nullable=True, comment="User who acknowledged the alert")  # ForeignKey("users.id") - temporarily disabled
    acknowledged_at = Column(DateTime, nullable=True, comment="When the alert was acknowledged")
    resolved_by = Column(UUIDType(), nullable=True, comment="User who resolved the alert")  # ForeignKey("users.id") - temporarily disabled
    resolved_at = Column(DateTime, nullable=True, comment="When the alert was resolved")
    alert_metadata = Column(JSON, nullable=True, comment="Additional metadata about the alert")
    
    # Relationships
    acknowledged_by_user = relationship("User", foreign_keys=[acknowledged_by], back_populates="acknowledged_alerts", lazy="select")
    resolved_by_user = relationship("User", foreign_keys=[resolved_by], back_populates="resolved_alerts", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_system_alert_name', 'alert_name'),
        Index('idx_system_alert_type', 'alert_type'),
        Index('idx_system_alert_severity', 'severity'),
        Index('idx_system_alert_status', 'status'),
        Index('idx_system_alert_source', 'source'),
        Index('idx_system_alert_created_at', 'created_at'),
        Index('idx_system_alert_severity_status', 'severity', 'status'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        alert_name: str,
        alert_type: str,
        severity: AlertSeverity,
        message: str,
        description: Optional[str] = None,
        source: Optional[str] = None,
        trigger_condition: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a System Alert.
        
        Args:
            alert_name: Name of the alert
            alert_type: Type of alert
            severity: Severity level of the alert
            message: Alert message
            description: Detailed description of the alert
            source: Source of the alert
            trigger_condition: Condition that triggered the alert
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.alert_name = alert_name
        self.alert_type = alert_type
        self.severity = severity.value if isinstance(severity, AlertSeverity) else severity
        self.message = message
        self.description = description
        self.source = source
        self.trigger_condition = trigger_condition
        self.status = AlertStatus.ACTIVE.value
        self._validate()
    
    def _validate(self):
        """Validate system alert business rules."""
        if not self.alert_name or not self.alert_name.strip():
            raise ValueError("Alert name cannot be empty")
        
        if len(self.alert_name) > 100:
            raise ValueError("Alert name cannot exceed 100 characters")
        
        if not self.alert_type or not self.alert_type.strip():
            raise ValueError("Alert type cannot be empty")
        
        if len(self.alert_type) > 20:
            raise ValueError("Alert type cannot exceed 20 characters")
        
        if self.severity not in [s.value for s in AlertSeverity]:
            raise ValueError(f"Invalid severity: {self.severity}")
        
        if not self.message or not self.message.strip():
            raise ValueError("Alert message cannot be empty")
        
        if self.source and len(self.source) > 100:
            raise ValueError("Source cannot exceed 100 characters")
    
    def acknowledge(self, acknowledged_by: str, notes: Optional[str] = None):
        """Acknowledge the alert."""
        self.status = AlertStatus.ACKNOWLEDGED.value
        self.acknowledged_by = acknowledged_by
        self.acknowledged_at = datetime.utcnow()
        
        if notes:
            self.resolution_notes = notes
    
    def resolve(self, resolved_by: str, resolution_notes: str):
        """Resolve the alert."""
        self.status = AlertStatus.RESOLVED.value
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = resolution_notes
    
    def suppress(self):
        """Suppress the alert."""
        self.status = AlertStatus.SUPPRESSED.value
    
    def is_active(self) -> bool:
        """Check if alert is active."""
        return self.status == AlertStatus.ACTIVE.value
    
    def is_resolved(self) -> bool:
        """Check if alert is resolved."""
        return self.status == AlertStatus.RESOLVED.value
    
    def is_critical(self) -> bool:
        """Check if alert is critical."""
        return self.severity == AlertSeverity.CRITICAL.value
    
    @property
    def display_name(self) -> str:
        """Get alert display name."""
        return f"{self.alert_name} ({self.severity})"
    
    @property
    def duration(self) -> Optional[int]:
        """Get alert duration in minutes."""
        if self.resolved_at:
            return int((self.resolved_at - self.created_at).total_seconds() / 60)
        return int((datetime.utcnow() - self.created_at).total_seconds() / 60)
    
    def __str__(self) -> str:
        """String representation of system alert."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of system alert."""
        return (
            f"SystemAlert(id={self.id}, name='{self.alert_name}', "
            f"severity='{self.severity}', status='{self.status}', "
            f"active={self.is_active})"
        )