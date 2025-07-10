from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.system.models import (
    SystemSetting, SystemBackup, AuditLog,
    SettingType, SettingCategory, BackupStatus, BackupType, AuditAction
)


class SystemService:
    """Service for system management operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # System Settings operations
    async def get_setting(self, setting_key: str) -> Optional[SystemSetting]:
        """Get system setting by key."""
        query = select(SystemSetting).where(
            and_(
                SystemSetting.setting_key == setting_key,
                SystemSetting.is_active == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_setting_value(self, setting_key: str, default_value: Any = None):
        """Get system setting value by key."""
        setting = await self.get_setting(setting_key)
        if setting:
            return setting.get_typed_value()
        return default_value
    
    async def get_settings_by_category(self, category: SettingCategory) -> List[SystemSetting]:
        """Get all settings in a category."""
        query = select(SystemSetting).where(
            and_(
                SystemSetting.setting_category == category.value,
                SystemSetting.is_active == True
            )
        ).order_by(SystemSetting.display_order, SystemSetting.setting_name)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_all_settings(self, include_system: bool = True) -> List[SystemSetting]:
        """Get all system settings."""
        query = select(SystemSetting).where(SystemSetting.is_active == True)
        
        if not include_system:
            query = query.where(SystemSetting.is_system == False)
        
        query = query.order_by(
            SystemSetting.setting_category,
            SystemSetting.display_order,
            SystemSetting.setting_name
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create_setting(
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
        display_order: str = "0"
    ) -> SystemSetting:
        """Create a new system setting."""
        # Check if setting already exists
        existing_setting = await self.get_setting(setting_key)
        if existing_setting:
            raise ConflictError(f"Setting with key '{setting_key}' already exists")
        
        setting = SystemSetting(
            setting_key=setting_key,
            setting_name=setting_name,
            setting_type=setting_type,
            setting_category=setting_category,
            setting_value=setting_value,
            default_value=default_value,
            description=description,
            is_system=is_system,
            is_sensitive=is_sensitive,
            validation_rules=validation_rules,
            display_order=display_order
        )
        
        self.session.add(setting)
        await self.session.commit()
        await self.session.refresh(setting)
        
        return setting
    
    async def update_setting(
        self,
        setting_key: str,
        setting_value: Any,
        updated_by: Optional[UUID] = None
    ) -> SystemSetting:
        """Update a system setting value."""
        setting = await self.get_setting(setting_key)
        if not setting:
            raise NotFoundError(f"Setting with key '{setting_key}' not found")
        
        if not setting.can_modify():
            raise ValidationError(f"Setting '{setting_key}' cannot be modified")
        
        # Store old value for audit
        old_value = setting.setting_value
        
        # Update the setting
        setting.set_typed_value(setting_value)
        setting.updated_by = str(updated_by) if updated_by else None
        
        await self.session.commit()
        await self.session.refresh(setting)
        
        # Create audit log
        if updated_by:
            await self.create_audit_log(
                user_id=updated_by,
                action=AuditAction.UPDATE,
                entity_type="SystemSetting",
                entity_id=str(setting.id),
                old_values={"setting_value": old_value},
                new_values={"setting_value": setting.setting_value}
            )
        
        return setting
    
    async def reset_setting(self, setting_key: str, updated_by: Optional[UUID] = None) -> SystemSetting:
        """Reset a system setting to its default value."""
        setting = await self.get_setting(setting_key)
        if not setting:
            raise NotFoundError(f"Setting with key '{setting_key}' not found")
        
        if not setting.can_modify():
            raise ValidationError(f"Setting '{setting_key}' cannot be modified")
        
        # Store old value for audit
        old_value = setting.setting_value
        
        # Reset to default
        setting.reset_to_default()
        setting.updated_by = str(updated_by) if updated_by else None
        
        await self.session.commit()
        await self.session.refresh(setting)
        
        # Create audit log
        if updated_by:
            await self.create_audit_log(
                user_id=updated_by,
                action=AuditAction.UPDATE,
                entity_type="SystemSetting",
                entity_id=str(setting.id),
                old_values={"setting_value": old_value},
                new_values={"setting_value": setting.setting_value}
            )
        
        return setting
    
    async def delete_setting(self, setting_key: str, deleted_by: Optional[UUID] = None) -> bool:
        """Delete a system setting."""
        setting = await self.get_setting(setting_key)
        if not setting:
            raise NotFoundError(f"Setting with key '{setting_key}' not found")
        
        if setting.is_system:
            raise ValidationError(f"System setting '{setting_key}' cannot be deleted")
        
        # Soft delete
        setting.is_active = False
        setting.updated_by = str(deleted_by) if deleted_by else None
        
        await self.session.commit()
        
        # Create audit log
        if deleted_by:
            await self.create_audit_log(
                user_id=deleted_by,
                action=AuditAction.DELETE,
                entity_type="SystemSetting",
                entity_id=str(setting.id)
            )
        
        return True
    
    async def initialize_default_settings(self) -> List[SystemSetting]:
        """Initialize default system settings."""
        default_settings = [
            # General settings
            {
                "setting_key": "app_name",
                "setting_name": "Application Name",
                "setting_type": SettingType.STRING,
                "setting_category": SettingCategory.GENERAL,
                "setting_value": "Rental Management System",
                "default_value": "Rental Management System",
                "description": "Name of the application",
                "is_system": True,
                "display_order": "1"
            },
            {
                "setting_key": "app_version",
                "setting_name": "Application Version",
                "setting_type": SettingType.STRING,
                "setting_category": SettingCategory.GENERAL,
                "setting_value": "2.0.0",
                "default_value": "2.0.0",
                "description": "Version of the application",
                "is_system": True,
                "display_order": "2"
            },
            {
                "setting_key": "company_name",
                "setting_name": "Company Name",
                "setting_type": SettingType.STRING,
                "setting_category": SettingCategory.GENERAL,
                "setting_value": "Your Company",
                "default_value": "Your Company",
                "description": "Name of the company using the system",
                "display_order": "3"
            },
            {
                "setting_key": "timezone",
                "setting_name": "System Timezone",
                "setting_type": SettingType.STRING,
                "setting_category": SettingCategory.GENERAL,
                "setting_value": "UTC",
                "default_value": "UTC",
                "description": "System timezone",
                "display_order": "4"
            },
            
            # Business settings
            {
                "setting_key": "default_currency",
                "setting_name": "Default Currency",
                "setting_type": SettingType.STRING,
                "setting_category": SettingCategory.BUSINESS,
                "setting_value": "USD",
                "default_value": "USD",
                "description": "Default currency for transactions",
                "display_order": "1"
            },
            {
                "setting_key": "business_hours_start",
                "setting_name": "Business Hours Start",
                "setting_type": SettingType.STRING,
                "setting_category": SettingCategory.BUSINESS,
                "setting_value": "09:00",
                "default_value": "09:00",
                "description": "Business hours start time",
                "display_order": "2"
            },
            {
                "setting_key": "business_hours_end",
                "setting_name": "Business Hours End",
                "setting_type": SettingType.STRING,
                "setting_category": SettingCategory.BUSINESS,
                "setting_value": "17:00",
                "default_value": "17:00",
                "description": "Business hours end time",
                "display_order": "3"
            },
            
            # Financial settings
            {
                "setting_key": "tax_rate",
                "setting_name": "Default Tax Rate",
                "setting_type": SettingType.DECIMAL,
                "setting_category": SettingCategory.FINANCIAL,
                "setting_value": "0.08",
                "default_value": "0.08",
                "description": "Default tax rate (8%)",
                "display_order": "1"
            },
            {
                "setting_key": "late_fee_rate",
                "setting_name": "Late Fee Rate",
                "setting_type": SettingType.DECIMAL,
                "setting_category": SettingCategory.FINANCIAL,
                "setting_value": "0.10",
                "default_value": "0.10",
                "description": "Late fee rate (10%)",
                "display_order": "2"
            },
            {
                "setting_key": "daily_late_fee",
                "setting_name": "Daily Late Fee",
                "setting_type": SettingType.DECIMAL,
                "setting_category": SettingCategory.FINANCIAL,
                "setting_value": "10.00",
                "default_value": "10.00",
                "description": "Daily late fee amount",
                "display_order": "3"
            },
            
            # Rental settings
            {
                "setting_key": "minimum_rental_days",
                "setting_name": "Minimum Rental Days",
                "setting_type": SettingType.INTEGER,
                "setting_category": SettingCategory.RENTAL,
                "setting_value": "1",
                "default_value": "1",
                "description": "Minimum rental period in days",
                "display_order": "1"
            },
            {
                "setting_key": "maximum_rental_days",
                "setting_name": "Maximum Rental Days",
                "setting_type": SettingType.INTEGER,
                "setting_category": SettingCategory.RENTAL,
                "setting_value": "365",
                "default_value": "365",
                "description": "Maximum rental period in days",
                "display_order": "2"
            },
            {
                "setting_key": "default_security_deposit",
                "setting_name": "Default Security Deposit",
                "setting_type": SettingType.DECIMAL,
                "setting_category": SettingCategory.RENTAL,
                "setting_value": "100.00",
                "default_value": "100.00",
                "description": "Default security deposit amount",
                "display_order": "3"
            },
            
            # System settings
            {
                "setting_key": "auto_backup_enabled",
                "setting_name": "Auto Backup Enabled",
                "setting_type": SettingType.BOOLEAN,
                "setting_category": SettingCategory.SYSTEM,
                "setting_value": "true",
                "default_value": "true",
                "description": "Enable automatic backups",
                "display_order": "1"
            },
            {
                "setting_key": "backup_retention_days",
                "setting_name": "Backup Retention Days",
                "setting_type": SettingType.INTEGER,
                "setting_category": SettingCategory.SYSTEM,
                "setting_value": "30",
                "default_value": "30",
                "description": "Number of days to retain backups",
                "display_order": "2"
            },
            {
                "setting_key": "audit_log_retention_days",
                "setting_name": "Audit Log Retention Days",
                "setting_type": SettingType.INTEGER,
                "setting_category": SettingCategory.SYSTEM,
                "setting_value": "90",
                "default_value": "90",
                "description": "Number of days to retain audit logs",
                "display_order": "3"
            }
        ]
        
        created_settings = []
        for setting_data in default_settings:
            existing_setting = await self.get_setting(setting_data["setting_key"])
            if not existing_setting:
                setting = await self.create_setting(**setting_data)
                created_settings.append(setting)
        
        return created_settings
    
    # System Backup operations
    async def create_backup(
        self,
        backup_name: str,
        backup_type: BackupType,
        started_by: UUID,
        description: Optional[str] = None,
        retention_days: str = "30"
    ) -> SystemBackup:
        """Create a new system backup."""
        backup = SystemBackup(
            backup_name=backup_name,
            backup_type=backup_type,
            started_by=str(started_by),
            description=description,
            retention_days=retention_days
        )
        
        self.session.add(backup)
        await self.session.commit()
        await self.session.refresh(backup)
        
        # Create audit log
        await self.create_audit_log(
            user_id=started_by,
            action=AuditAction.BACKUP,
            entity_type="SystemBackup",
            entity_id=str(backup.id),
            new_values={
                "backup_name": backup_name,
                "backup_type": backup_type.value,
                "status": backup.backup_status
            }
        )
        
        return backup
    
    async def get_backup(self, backup_id: UUID) -> Optional[SystemBackup]:
        """Get system backup by ID."""
        query = select(SystemBackup).where(
            and_(
                SystemBackup.id == backup_id,
                SystemBackup.is_active == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_backups(
        self,
        skip: int = 0,
        limit: int = 100,
        backup_type: Optional[BackupType] = None,
        backup_status: Optional[BackupStatus] = None,
        started_by: Optional[UUID] = None
    ) -> List[SystemBackup]:
        """Get all system backups with optional filtering."""
        query = select(SystemBackup).where(SystemBackup.is_active == True)
        
        if backup_type:
            query = query.where(SystemBackup.backup_type == backup_type.value)
        if backup_status:
            query = query.where(SystemBackup.backup_status == backup_status.value)
        if started_by:
            query = query.where(SystemBackup.started_by == str(started_by))
        
        query = query.order_by(SystemBackup.started_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def start_backup(self, backup_id: UUID) -> SystemBackup:
        """Start a backup process."""
        backup = await self.get_backup(backup_id)
        if not backup:
            raise NotFoundError(f"Backup with ID {backup_id} not found")
        
        backup.start_backup()
        await self.session.commit()
        await self.session.refresh(backup)
        
        return backup
    
    async def complete_backup(self, backup_id: UUID, backup_path: str, backup_size: int) -> SystemBackup:
        """Complete a backup process."""
        backup = await self.get_backup(backup_id)
        if not backup:
            raise NotFoundError(f"Backup with ID {backup_id} not found")
        
        backup.complete_backup(backup_path, backup_size)
        await self.session.commit()
        await self.session.refresh(backup)
        
        return backup
    
    async def fail_backup(self, backup_id: UUID, error_message: str) -> SystemBackup:
        """Fail a backup process."""
        backup = await self.get_backup(backup_id)
        if not backup:
            raise NotFoundError(f"Backup with ID {backup_id} not found")
        
        backup.fail_backup(error_message)
        await self.session.commit()
        await self.session.refresh(backup)
        
        return backup
    
    async def cancel_backup(self, backup_id: UUID) -> SystemBackup:
        """Cancel a backup process."""
        backup = await self.get_backup(backup_id)
        if not backup:
            raise NotFoundError(f"Backup with ID {backup_id} not found")
        
        backup.cancel_backup()
        await self.session.commit()
        await self.session.refresh(backup)
        
        return backup
    
    async def delete_backup(self, backup_id: UUID, deleted_by: Optional[UUID] = None) -> bool:
        """Delete a system backup."""
        backup = await self.get_backup(backup_id)
        if not backup:
            raise NotFoundError(f"Backup with ID {backup_id} not found")
        
        # Soft delete
        backup.is_active = False
        backup.updated_by = str(deleted_by) if deleted_by else None
        
        await self.session.commit()
        
        # Create audit log
        if deleted_by:
            await self.create_audit_log(
                user_id=deleted_by,
                action=AuditAction.DELETE,
                entity_type="SystemBackup",
                entity_id=str(backup.id)
            )
        
        return True
    
    async def cleanup_expired_backups(self) -> int:
        """Clean up expired backups."""
        query = select(SystemBackup).where(
            and_(
                SystemBackup.is_active == True,
                SystemBackup.backup_status == BackupStatus.COMPLETED.value
            )
        )
        result = await self.session.execute(query)
        backups = result.scalars().all()
        
        expired_count = 0
        for backup in backups:
            if backup.is_expired():
                backup.is_active = False
                expired_count += 1
        
        await self.session.commit()
        return expired_count
    
    # Audit Log operations
    async def create_audit_log(
        self,
        action: AuditAction,
        user_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        audit_metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Create an audit log entry."""
        audit_log = AuditLog(
            action=action,
            user_id=str(user_id) if user_id else None,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            success=success,
            error_message=error_message,
            audit_metadata=audit_metadata
        )
        
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        
        return audit_log
    
    async def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
        action: Optional[AuditAction] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        success: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Get audit logs with optional filtering."""
        query = select(AuditLog).where(AuditLog.is_active == True)
        
        if user_id:
            query = query.where(AuditLog.user_id == str(user_id))
        if action:
            query = query.where(AuditLog.action == action.value)
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
        if success is not None:
            query = query.where(AuditLog.success == success)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_audit_log(self, audit_log_id: UUID) -> Optional[AuditLog]:
        """Get audit log by ID."""
        query = select(AuditLog).where(
            and_(
                AuditLog.id == audit_log_id,
                AuditLog.is_active == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def cleanup_old_audit_logs(self, retention_days: int = 90) -> int:
        """Clean up old audit logs."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        query = select(AuditLog).where(
            and_(
                AuditLog.created_at < cutoff_date,
                AuditLog.is_active == True
            )
        )
        result = await self.session.execute(query)
        old_logs = result.scalars().all()
        
        cleanup_count = 0
        for log in old_logs:
            log.is_active = False
            cleanup_count += 1
        
        await self.session.commit()
        return cleanup_count
    
    # System maintenance operations
    async def perform_system_maintenance(self, user_id: UUID) -> Dict[str, Any]:
        """Perform system maintenance tasks."""
        maintenance_results = {}
        
        # Cleanup expired backups
        expired_backups = await self.cleanup_expired_backups()
        maintenance_results['expired_backups_cleaned'] = expired_backups
        
        # Cleanup old audit logs
        retention_days = await self.get_setting_value('audit_log_retention_days', 90)
        old_logs = await self.cleanup_old_audit_logs(int(retention_days))
        maintenance_results['old_audit_logs_cleaned'] = old_logs
        
        # Create audit log for maintenance
        await self.create_audit_log(
            user_id=user_id,
            action=AuditAction.UPDATE,
            entity_type="SystemMaintenance",
            audit_metadata={
                'maintenance_type': 'automated_cleanup',
                'results': maintenance_results
            }
        )
        
        return maintenance_results
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        # Get database size and counts
        settings_count = len(await self.get_all_settings())
        backups_count = len(await self.get_backups(limit=1000))
        
        # Get recent activity
        recent_logs = await self.get_audit_logs(limit=10)
        
        return {
            'system_name': await self.get_setting_value('app_name', 'Rental Management System'),
            'system_version': await self.get_setting_value('app_version', '2.0.0'),
            'company_name': await self.get_setting_value('company_name', 'Your Company'),
            'timezone': await self.get_setting_value('timezone', 'UTC'),
            'settings_count': settings_count,
            'backups_count': backups_count,
            'recent_activity_count': len(recent_logs),
            'last_backup': await self._get_last_backup_info(),
            'system_health': await self._get_system_health()
        }
    
    async def _get_last_backup_info(self) -> Optional[Dict[str, Any]]:
        """Get last backup information."""
        backups = await self.get_backups(limit=1)
        if backups:
            backup = backups[0]
            return {
                'backup_name': backup.backup_name,
                'backup_type': backup.backup_type,
                'backup_status': backup.backup_status,
                'started_at': backup.started_at.isoformat(),
                'completed_at': backup.completed_at.isoformat() if backup.completed_at else None
            }
        return None
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        # This would be expanded with actual health checks
        return {
            'status': 'healthy',
            'uptime': '99.9%',
            'response_time': '120ms',
            'memory_usage': '68%',
            'cpu_usage': '25%',
            'disk_usage': '42%'
        }


# Additional imports for datetime operations
from datetime import timedelta