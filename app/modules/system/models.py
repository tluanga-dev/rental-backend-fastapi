from enum import Enum
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base import BaseModel, UUIDType


class SettingType(str, Enum):
    """Setting type enumeration."""
    STRING = "STRING"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    DATE = "DATE"
    DATETIME = "DATETIME"


class SettingCategory(str, Enum):
    """Setting category enumeration."""
    GENERAL = "GENERAL"
    BUSINESS = "BUSINESS"
    FINANCIAL = "FINANCIAL"
    INVENTORY = "INVENTORY"
    RENTAL = "RENTAL"
    NOTIFICATION = "NOTIFICATION"
    SECURITY = "SECURITY"
    INTEGRATION = "INTEGRATION"
    REPORTING = "REPORTING"
    SYSTEM = "SYSTEM"


class BackupStatus(str, Enum):
    """Backup status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BackupType(str, Enum):
    """Backup type enumeration."""
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"
    DIFFERENTIAL = "DIFFERENTIAL"


class AuditAction(str, Enum):
    """Audit action enumeration."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"


class SystemSetting(BaseModel):
    """
    System setting model for application configuration.
    
    Attributes:
        setting_key: Unique setting key
        setting_name: Human-readable setting name
        setting_type: Type of setting (STRING, INTEGER, etc.)
        setting_category: Category of setting (GENERAL, BUSINESS, etc.)
        setting_value: Current value of the setting
        default_value: Default value of the setting
        description: Description of the setting
        is_system: Whether this is a system setting (read-only)
        is_sensitive: Whether this setting contains sensitive data
        validation_rules: JSON validation rules for the setting
        display_order: Order for displaying settings
    """
    
    __tablename__ = "system_settings"
    
    setting_key = Column(String(100), nullable=False, unique=True, index=True, comment="Unique setting key")
    setting_name = Column(String(200), nullable=False, comment="Human-readable setting name")
    setting_type = Column(String(20), nullable=False, comment="Type of setting")
    setting_category = Column(String(20), nullable=False, comment="Category of setting")
    setting_value = Column(Text, nullable=True, comment="Current value of the setting")
    default_value = Column(Text, nullable=True, comment="Default value of the setting")
    description = Column(Text, nullable=True, comment="Description of the setting")
    is_system = Column(Boolean, nullable=False, default=False, comment="System setting flag")
    is_sensitive = Column(Boolean, nullable=False, default=False, comment="Sensitive data flag")
    validation_rules = Column(JSON, nullable=True, comment="JSON validation rules")
    display_order = Column(String(10), nullable=False, default="0", comment="Display order")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_system_setting_key', 'setting_key'),
        Index('idx_system_setting_category', 'setting_category'),
        Index('idx_system_setting_type', 'setting_type'),
        Index('idx_system_setting_system', 'is_system'),
        Index('idx_system_setting_display_order', 'display_order'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        setting_key: str,
        setting_name: str,
        setting_type: SettingType,
        setting_category: SettingCategory,
        setting_value: Optional[str] = None,
        default_value: Optional[str] = None,
        description: Optional[str] = None,
        is_system: bool = False,
        is_sensitive: bool = False,
        validation_rules: Optional[Dict[str, Any]] = None,
        display_order: str = "0",
        **kwargs
    ):
        """
        Initialize a System Setting.
        
        Args:
            setting_key: Unique setting key
            setting_name: Human-readable setting name
            setting_type: Type of setting
            setting_category: Category of setting
            setting_value: Current value of the setting
            default_value: Default value of the setting
            description: Description of the setting
            is_system: Whether this is a system setting
            is_sensitive: Whether this setting contains sensitive data
            validation_rules: JSON validation rules
            display_order: Display order
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.setting_key = setting_key
        self.setting_name = setting_name
        self.setting_type = setting_type.value if isinstance(setting_type, SettingType) else setting_type
        self.setting_category = setting_category.value if isinstance(setting_category, SettingCategory) else setting_category
        self.setting_value = setting_value
        self.default_value = default_value
        self.description = description
        self.is_system = is_system
        self.is_sensitive = is_sensitive
        self.validation_rules = validation_rules or {}
        self.display_order = display_order
        self._validate()
    
    def _validate(self):
        """Validate system setting business rules."""
        if not self.setting_key or not self.setting_key.strip():
            raise ValueError("Setting key cannot be empty")
        
        if len(self.setting_key) > 100:
            raise ValueError("Setting key cannot exceed 100 characters")
        
        if not self.setting_name or not self.setting_name.strip():
            raise ValueError("Setting name cannot be empty")
        
        if len(self.setting_name) > 200:
            raise ValueError("Setting name cannot exceed 200 characters")
        
        if self.setting_type not in [st.value for st in SettingType]:
            raise ValueError(f"Invalid setting type: {self.setting_type}")
        
        if self.setting_category not in [sc.value for sc in SettingCategory]:
            raise ValueError(f"Invalid setting category: {self.setting_category}")
        
        # Validate display order is numeric
        try:
            int(self.display_order)
        except ValueError:
            raise ValueError("Display order must be a valid number")
    
    def get_typed_value(self):
        """Get the setting value converted to its proper type."""
        if self.setting_value is None:
            return None
        
        if self.setting_type == SettingType.STRING.value:
            return str(self.setting_value)
        elif self.setting_type == SettingType.INTEGER.value:
            return int(self.setting_value)
        elif self.setting_type == SettingType.DECIMAL.value:
            return Decimal(self.setting_value)
        elif self.setting_type == SettingType.BOOLEAN.value:
            return str(self.setting_value).lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == SettingType.JSON.value:
            import json
            return json.loads(self.setting_value)
        elif self.setting_type == SettingType.DATE.value:
            return datetime.strptime(self.setting_value, '%Y-%m-%d').date()
        elif self.setting_type == SettingType.DATETIME.value:
            return datetime.fromisoformat(self.setting_value)
        else:
            return self.setting_value
    
    def set_typed_value(self, value):
        """Set the setting value from a typed value."""
        if value is None:
            self.setting_value = None
            return
        
        if self.setting_type == SettingType.STRING.value:
            self.setting_value = str(value)
        elif self.setting_type == SettingType.INTEGER.value:
            self.setting_value = str(int(value))
        elif self.setting_type == SettingType.DECIMAL.value:
            self.setting_value = str(Decimal(value))
        elif self.setting_type == SettingType.BOOLEAN.value:
            self.setting_value = str(bool(value)).lower()
        elif self.setting_type == SettingType.JSON.value:
            import json
            self.setting_value = json.dumps(value)
        elif self.setting_type == SettingType.DATE.value:
            if isinstance(value, date):
                self.setting_value = value.strftime('%Y-%m-%d')
            else:
                self.setting_value = str(value)
        elif self.setting_type == SettingType.DATETIME.value:
            if isinstance(value, datetime):
                self.setting_value = value.isoformat()
            else:
                self.setting_value = str(value)
        else:
            self.setting_value = str(value)
    
    def reset_to_default(self):
        """Reset setting to default value."""
        self.setting_value = self.default_value
    
    def is_default(self) -> bool:
        """Check if setting is at default value."""
        return self.setting_value == self.default_value
    
    def can_modify(self) -> bool:
        """Check if setting can be modified."""
        return not self.is_system and self.is_active
    
    @property
    def display_name(self) -> str:
        """Get setting display name."""
        return self.setting_name
    
    @property
    def masked_value(self) -> str:
        """Get masked value for sensitive settings."""
        if self.is_sensitive and self.setting_value:
            return "***MASKED***"
        return self.setting_value or ""
    
    def __str__(self) -> str:
        """String representation of system setting."""
        return f"{self.setting_name} ({self.setting_key})"
    
    def __repr__(self) -> str:
        """Developer representation of system setting."""
        return (
            f"SystemSetting(id={self.id}, key='{self.setting_key}', "
            f"name='{self.setting_name}', type='{self.setting_type}', "
            f"category='{self.setting_category}', active={self.is_active})"
        )


class SystemBackup(BaseModel):
    """
    System backup model for database and file backups.
    
    Attributes:
        backup_name: Name of the backup
        backup_type: Type of backup (FULL, INCREMENTAL, DIFFERENTIAL)
        backup_status: Current status of the backup
        backup_path: Path to the backup file
        backup_size: Size of the backup file in bytes
        started_by: User who started the backup
        started_at: When the backup was started
        completed_at: When the backup was completed
        error_message: Error message if backup failed
        retention_days: Number of days to retain the backup
        description: Description of the backup
        backup_metadata: Additional metadata about the backup
    """
    
    __tablename__ = "system_backups"
    
    backup_name = Column(String(200), nullable=False, comment="Name of the backup")
    backup_type = Column(String(20), nullable=False, comment="Type of backup")
    backup_status = Column(String(20), nullable=False, default=BackupStatus.PENDING.value, comment="Current status")
    backup_path = Column(String(500), nullable=True, comment="Path to the backup file")
    backup_size = Column(String(20), nullable=True, comment="Size of the backup file")
    started_by = Column(UUIDType(), nullable=False, comment="User who started the backup")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="When backup was started")
    completed_at = Column(DateTime, nullable=True, comment="When backup was completed")
    error_message = Column(Text, nullable=True, comment="Error message if backup failed")
    retention_days = Column(String(10), nullable=False, default="30", comment="Days to retain backup")
    description = Column(Text, nullable=True, comment="Description of the backup")
    backup_metadata = Column(JSON, nullable=True, comment="Additional metadata about the backup")
    
    # Relationships
    # started_by_user = relationship("User", back_populates="started_backups", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_system_backup_name', 'backup_name'),
        Index('idx_system_backup_type', 'backup_type'),
        Index('idx_system_backup_status', 'backup_status'),
        Index('idx_system_backup_started_by', 'started_by'),
        Index('idx_system_backup_started_at', 'started_at'),
        Index('idx_system_backup_completed_at', 'completed_at'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        backup_name: str,
        backup_type: BackupType,
        started_by: str,
        description: Optional[str] = None,
        retention_days: str = "30",
        **kwargs
    ):
        """
        Initialize a System Backup.
        
        Args:
            backup_name: Name of the backup
            backup_type: Type of backup
            started_by: User who started the backup
            description: Description of the backup
            retention_days: Days to retain backup
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.backup_name = backup_name
        self.backup_type = backup_type.value if isinstance(backup_type, BackupType) else backup_type
        self.started_by = started_by
        self.description = description
        self.retention_days = retention_days
        self.started_at = datetime.utcnow()
        self.backup_status = BackupStatus.PENDING.value
        self._validate()
    
    def _validate(self):
        """Validate system backup business rules."""
        if not self.backup_name or not self.backup_name.strip():
            raise ValueError("Backup name cannot be empty")
        
        if len(self.backup_name) > 200:
            raise ValueError("Backup name cannot exceed 200 characters")
        
        if self.backup_type not in [bt.value for bt in BackupType]:
            raise ValueError(f"Invalid backup type: {self.backup_type}")
        
        # Validate retention days is numeric
        try:
            days = int(self.retention_days)
            if days < 1:
                raise ValueError("Retention days must be at least 1")
        except ValueError:
            raise ValueError("Retention days must be a valid positive number")
    
    def start_backup(self):
        """Start the backup process."""
        self.backup_status = BackupStatus.RUNNING.value
        self.started_at = datetime.utcnow()
    
    def complete_backup(self, backup_path: str, backup_size: int):
        """Complete the backup process."""
        self.backup_status = BackupStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.backup_path = backup_path
        self.backup_size = str(backup_size)
        self.error_message = None
    
    def fail_backup(self, error_message: str):
        """Fail the backup process."""
        self.backup_status = BackupStatus.FAILED.value
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def cancel_backup(self):
        """Cancel the backup process."""
        self.backup_status = BackupStatus.CANCELLED.value
        self.completed_at = datetime.utcnow()
    
    def is_completed(self) -> bool:
        """Check if backup is completed."""
        return self.backup_status == BackupStatus.COMPLETED.value
    
    def is_running(self) -> bool:
        """Check if backup is running."""
        return self.backup_status == BackupStatus.RUNNING.value
    
    def is_failed(self) -> bool:
        """Check if backup failed."""
        return self.backup_status == BackupStatus.FAILED.value
    
    def is_expired(self) -> bool:
        """Check if backup is expired based on retention policy."""
        if not self.completed_at:
            return False
        
        try:
            retention_days = int(self.retention_days)
            expiry_date = self.completed_at + timedelta(days=retention_days)
            return datetime.utcnow() > expiry_date
        except ValueError:
            return False
    
    @property
    def display_name(self) -> str:
        """Get backup display name."""
        return f"{self.backup_name} ({self.backup_type})"
    
    @property
    def backup_size_mb(self) -> Optional[float]:
        """Get backup size in MB."""
        if self.backup_size:
            try:
                return float(self.backup_size) / (1024 * 1024)
            except ValueError:
                return None
        return None
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Get backup duration in minutes."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() / 60)
        return None
    
    def __str__(self) -> str:
        """String representation of system backup."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of system backup."""
        return (
            f"SystemBackup(id={self.id}, name='{self.backup_name}', "
            f"type='{self.backup_type}', status='{self.backup_status}', "
            f"active={self.is_active})"
        )


class AuditLog(BaseModel):
    """
    Audit log model for tracking system activities.
    
    Attributes:
        user_id: User who performed the action
        action: Action performed
        entity_type: Type of entity affected
        entity_id: ID of the entity affected
        old_values: Old values before the action
        new_values: New values after the action
        ip_address: IP address of the user
        user_agent: User agent string
        session_id: Session ID
        success: Whether the action was successful
        error_message: Error message if action failed
        audit_metadata: Additional metadata about the action
    """
    
    __tablename__ = "audit_logs"
    
    user_id = Column(UUIDType(), nullable=True, comment="User who performed the action")
    action = Column(String(50), nullable=False, comment="Action performed")
    entity_type = Column(String(100), nullable=True, comment="Type of entity affected")
    entity_id = Column(UUIDType(), nullable=True, comment="ID of the entity affected")
    old_values = Column(JSON, nullable=True, comment="Old values before the action")
    new_values = Column(JSON, nullable=True, comment="New values after the action")
    ip_address = Column(String(45), nullable=True, comment="IP address of the user")
    user_agent = Column(Text, nullable=True, comment="User agent string")
    session_id = Column(String(100), nullable=True, comment="Session ID")
    success = Column(Boolean, nullable=False, default=True, comment="Whether action was successful")
    error_message = Column(Text, nullable=True, comment="Error message if action failed")
    audit_metadata = Column(JSON, nullable=True, comment="Additional metadata about the action")
    
    # Relationships
    # user = relationship("User", back_populates="audit_logs", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_audit_log_user_id', 'user_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_entity_type', 'entity_type'),
        Index('idx_audit_log_entity_id', 'entity_id'),
        Index('idx_audit_log_created_at', 'created_at'),
        Index('idx_audit_log_success', 'success'),
        Index('idx_audit_log_ip_address', 'ip_address'),
        Index('idx_audit_log_session_id', 'session_id'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        audit_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize an Audit Log.
        
        Args:
            action: Action performed
            user_id: User who performed the action
            entity_type: Type of entity affected
            entity_id: ID of the entity affected
            old_values: Old values before the action
            new_values: New values after the action
            ip_address: IP address of the user
            user_agent: User agent string
            session_id: Session ID
            success: Whether the action was successful
            error_message: Error message if action failed
            audit_metadata: Additional metadata about the action
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.action = action.value if isinstance(action, AuditAction) else action
        self.user_id = user_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.old_values = old_values or {}
        self.new_values = new_values or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.session_id = session_id
        self.success = success
        self.error_message = error_message
        self.audit_metadata = audit_metadata or {}
        self._validate()
    
    def _validate(self):
        """Validate audit log business rules."""
        if not self.action or not self.action.strip():
            raise ValueError("Action cannot be empty")
        
        if len(self.action) > 50:
            raise ValueError("Action cannot exceed 50 characters")
        
        if self.entity_type and len(self.entity_type) > 100:
            raise ValueError("Entity type cannot exceed 100 characters")
        
        if self.ip_address and len(self.ip_address) > 45:
            raise ValueError("IP address cannot exceed 45 characters")
        
        if self.session_id and len(self.session_id) > 100:
            raise ValueError("Session ID cannot exceed 100 characters")
    
    def is_successful(self) -> bool:
        """Check if action was successful."""
        return self.success
    
    def has_changes(self) -> bool:
        """Check if there are any changes recorded."""
        return bool(self.old_values or self.new_values)
    
    def get_changes(self) -> Dict[str, Any]:
        """Get the changes made."""
        changes = {}
        
        if self.old_values and self.new_values:
            for key in set(self.old_values.keys()) | set(self.new_values.keys()):
                old_value = self.old_values.get(key)
                new_value = self.new_values.get(key)
                
                if old_value != new_value:
                    changes[key] = {
                        'old': old_value,
                        'new': new_value
                    }
        
        return changes
    
    @property
    def display_name(self) -> str:
        """Get audit log display name."""
        entity_info = ""
        if self.entity_type and self.entity_id:
            entity_info = f" on {self.entity_type} {self.entity_id}"
        
        return f"{self.action}{entity_info}"
    
    @property
    def status_display(self) -> str:
        """Get status display."""
        return "SUCCESS" if self.success else "FAILED"
    
    def __str__(self) -> str:
        """String representation of audit log."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of audit log."""
        return (
            f"AuditLog(id={self.id}, action='{self.action}', "
            f"user_id={self.user_id}, entity_type='{self.entity_type}', "
            f"success={self.success}, active={self.is_active})"
        )


# Additional imports for datetime operations
from datetime import timedelta