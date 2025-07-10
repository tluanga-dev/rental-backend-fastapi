from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.shared.dependencies import get_session
from app.modules.system.service import SystemService
from app.modules.system.models import (
    SettingType, SettingCategory, BackupStatus, BackupType, AuditAction
)


router = APIRouter(prefix="/system", tags=["System Management"])


# Response models
class SystemSettingResponse(BaseModel):
    """Response model for system settings."""
    id: UUID
    setting_key: str
    setting_name: str
    setting_type: SettingType
    setting_category: SettingCategory
    setting_value: Optional[str]
    default_value: Optional[str]
    description: Optional[str]
    is_system: bool
    is_sensitive: bool
    validation_rules: Optional[Dict[str, Any]]
    display_order: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SystemBackupResponse(BaseModel):
    """Response model for system backups."""
    id: UUID
    backup_name: str
    backup_type: BackupType
    backup_status: BackupStatus
    backup_path: Optional[str]
    backup_size: Optional[str]
    started_by: UUID
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    retention_days: str
    description: Optional[str]
    backup_metadata: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Response model for audit logs."""
    id: UUID
    user_id: Optional[UUID]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    success: bool
    error_message: Optional[str]
    audit_metadata: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Request models
class SystemSettingCreateRequest(BaseModel):
    """Request model for creating system settings."""
    setting_key: str
    setting_name: str
    setting_type: SettingType
    setting_category: SettingCategory
    setting_value: Optional[str] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    is_system: bool = False
    is_sensitive: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    display_order: str = "0"


class SystemSettingUpdateRequest(BaseModel):
    """Request model for updating system settings."""
    setting_value: Any


class SystemBackupCreateRequest(BaseModel):
    """Request model for creating system backups."""
    backup_name: str
    backup_type: BackupType
    description: Optional[str] = None
    retention_days: str = "30"


class SystemInfoResponse(BaseModel):
    """Response model for system information."""
    system_name: str
    system_version: str
    company_name: str
    timezone: str
    settings_count: int
    backups_count: int
    recent_activity_count: int
    last_backup: Optional[Dict[str, Any]]
    system_health: Dict[str, Any]


# Dependency to get system service
async def get_system_service(session: AsyncSession = Depends(get_session)) -> SystemService:
    return SystemService(session)


# System Settings endpoints
@router.get("/settings", response_model=List[SystemSettingResponse])
async def get_settings(
    category: Optional[SettingCategory] = Query(None, description="Filter by category"),
    include_system: bool = Query(True, description="Include system settings"),
    service: SystemService = Depends(get_system_service)
):
    """Get all system settings."""
    try:
        if category:
            settings = await service.get_settings_by_category(category)
        else:
            settings = await service.get_all_settings(include_system)
        
        return [SystemSettingResponse.model_validate(setting) for setting in settings]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/settings/{setting_key}", response_model=SystemSettingResponse)
async def get_setting(
    setting_key: str,
    service: SystemService = Depends(get_system_service)
):
    """Get system setting by key."""
    try:
        setting = await service.get_setting(setting_key)
        if not setting:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{setting_key}' not found")
        
        return SystemSettingResponse.model_validate(setting)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/settings/{setting_key}/value")
async def get_setting_value(
    setting_key: str,
    service: SystemService = Depends(get_system_service)
):
    """Get system setting value by key."""
    try:
        value = await service.get_setting_value(setting_key)
        if value is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{setting_key}' not found")
        
        return {"setting_key": setting_key, "value": value}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/settings", response_model=SystemSettingResponse, status_code=status.HTTP_201_CREATED)
async def create_setting(
    setting_data: SystemSettingCreateRequest,
    service: SystemService = Depends(get_system_service)
):
    """Create a new system setting."""
    try:
        setting = await service.create_setting(
            setting_key=setting_data.setting_key,
            setting_name=setting_data.setting_name,
            setting_type=setting_data.setting_type,
            setting_category=setting_data.setting_category,
            setting_value=setting_data.setting_value,
            default_value=setting_data.default_value,
            description=setting_data.description,
            is_system=setting_data.is_system,
            is_sensitive=setting_data.is_sensitive,
            validation_rules=setting_data.validation_rules,
            display_order=setting_data.display_order
        )
        
        return SystemSettingResponse.model_validate(setting)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/settings/{setting_key}", response_model=SystemSettingResponse)
async def update_setting(
    setting_key: str,
    setting_data: SystemSettingUpdateRequest,
    updated_by: UUID = Query(..., description="User ID updating the setting"),
    service: SystemService = Depends(get_system_service)
):
    """Update a system setting value."""
    try:
        setting = await service.update_setting(setting_key, setting_data.setting_value, updated_by)
        return SystemSettingResponse.model_validate(setting)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/settings/{setting_key}/reset", response_model=SystemSettingResponse)
async def reset_setting(
    setting_key: str,
    updated_by: UUID = Query(..., description="User ID resetting the setting"),
    service: SystemService = Depends(get_system_service)
):
    """Reset a system setting to its default value."""
    try:
        setting = await service.reset_setting(setting_key, updated_by)
        return SystemSettingResponse.model_validate(setting)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/settings/{setting_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    setting_key: str,
    deleted_by: UUID = Query(..., description="User ID deleting the setting"),
    service: SystemService = Depends(get_system_service)
):
    """Delete a system setting."""
    try:
        success = await service.delete_setting(setting_key, deleted_by)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{setting_key}' not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/settings/initialize", response_model=List[SystemSettingResponse])
async def initialize_default_settings(
    service: SystemService = Depends(get_system_service)
):
    """Initialize default system settings."""
    try:
        settings = await service.initialize_default_settings()
        return [SystemSettingResponse.model_validate(setting) for setting in settings]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# System Backup endpoints
@router.post("/backups", response_model=SystemBackupResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    backup_data: SystemBackupCreateRequest,
    started_by: UUID = Query(..., description="User ID starting the backup"),
    service: SystemService = Depends(get_system_service)
):
    """Create a new system backup."""
    try:
        backup = await service.create_backup(
            backup_name=backup_data.backup_name,
            backup_type=backup_data.backup_type,
            started_by=started_by,
            description=backup_data.description,
            retention_days=backup_data.retention_days
        )
        
        return SystemBackupResponse.model_validate(backup)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/backups", response_model=List[SystemBackupResponse])
async def get_backups(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    backup_type: Optional[BackupType] = Query(None, description="Filter by backup type"),
    backup_status: Optional[BackupStatus] = Query(None, description="Filter by backup status"),
    started_by: Optional[UUID] = Query(None, description="Filter by starter"),
    service: SystemService = Depends(get_system_service)
):
    """Get all system backups with optional filtering."""
    try:
        backups = await service.get_backups(
            skip=skip,
            limit=limit,
            backup_type=backup_type,
            backup_status=backup_status,
            started_by=started_by
        )
        
        return [SystemBackupResponse.model_validate(backup) for backup in backups]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/backups/{backup_id}", response_model=SystemBackupResponse)
async def get_backup(
    backup_id: UUID,
    service: SystemService = Depends(get_system_service)
):
    """Get system backup by ID."""
    try:
        backup = await service.get_backup(backup_id)
        if not backup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Backup with ID {backup_id} not found")
        
        return SystemBackupResponse.model_validate(backup)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/backups/{backup_id}/start", response_model=SystemBackupResponse)
async def start_backup(
    backup_id: UUID,
    service: SystemService = Depends(get_system_service)
):
    """Start a backup process."""
    try:
        backup = await service.start_backup(backup_id)
        return SystemBackupResponse.model_validate(backup)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/backups/{backup_id}/complete", response_model=SystemBackupResponse)
async def complete_backup(
    backup_id: UUID,
    backup_path: str = Query(..., description="Path to the backup file"),
    backup_size: int = Query(..., description="Size of the backup file in bytes"),
    service: SystemService = Depends(get_system_service)
):
    """Complete a backup process."""
    try:
        backup = await service.complete_backup(backup_id, backup_path, backup_size)
        return SystemBackupResponse.model_validate(backup)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/backups/{backup_id}/fail", response_model=SystemBackupResponse)
async def fail_backup(
    backup_id: UUID,
    error_message: str = Query(..., description="Error message"),
    service: SystemService = Depends(get_system_service)
):
    """Fail a backup process."""
    try:
        backup = await service.fail_backup(backup_id, error_message)
        return SystemBackupResponse.model_validate(backup)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/backups/{backup_id}/cancel", response_model=SystemBackupResponse)
async def cancel_backup(
    backup_id: UUID,
    service: SystemService = Depends(get_system_service)
):
    """Cancel a backup process."""
    try:
        backup = await service.cancel_backup(backup_id)
        return SystemBackupResponse.model_validate(backup)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/backups/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    backup_id: UUID,
    deleted_by: UUID = Query(..., description="User ID deleting the backup"),
    service: SystemService = Depends(get_system_service)
):
    """Delete a system backup."""
    try:
        success = await service.delete_backup(backup_id, deleted_by)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Backup with ID {backup_id} not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/backups/cleanup-expired")
async def cleanup_expired_backups(
    service: SystemService = Depends(get_system_service)
):
    """Clean up expired backups."""
    try:
        cleaned_count = await service.cleanup_expired_backups()
        return {"message": f"Cleaned up {cleaned_count} expired backups"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Audit Log endpoints
@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    service: SystemService = Depends(get_system_service)
):
    """Get audit logs with optional filtering."""
    try:
        # Convert action string to enum if provided
        action_enum = None
        if action:
            try:
                action_enum = AuditAction(action)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid action: {action}")
        
        logs = await service.get_audit_logs(
            skip=skip,
            limit=limit,
            user_id=user_id,
            action=action_enum,
            entity_type=entity_type,
            entity_id=entity_id,
            success=success,
            start_date=start_date,
            end_date=end_date
        )
        
        return [AuditLogResponse.model_validate(log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/audit-logs/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_log_id: UUID,
    service: SystemService = Depends(get_system_service)
):
    """Get audit log by ID."""
    try:
        log = await service.get_audit_log(audit_log_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audit log with ID {audit_log_id} not found")
        
        return AuditLogResponse.model_validate(log)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/audit-logs/cleanup")
async def cleanup_old_audit_logs(
    retention_days: int = Query(90, ge=1, description="Days to retain audit logs"),
    service: SystemService = Depends(get_system_service)
):
    """Clean up old audit logs."""
    try:
        cleaned_count = await service.cleanup_old_audit_logs(retention_days)
        return {"message": f"Cleaned up {cleaned_count} old audit logs"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# System Information and Maintenance endpoints
@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info(
    service: SystemService = Depends(get_system_service)
):
    """Get system information."""
    try:
        info = await service.get_system_info()
        return SystemInfoResponse.model_validate(info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/maintenance")
async def perform_maintenance(
    user_id: UUID = Query(..., description="User ID performing maintenance"),
    service: SystemService = Depends(get_system_service)
):
    """Perform system maintenance tasks."""
    try:
        results = await service.perform_system_maintenance(user_id)
        return {"message": "System maintenance completed", "results": results}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Settings by category endpoints
@router.get("/settings/categories/{category}", response_model=List[SystemSettingResponse])
async def get_settings_by_category(
    category: SettingCategory,
    service: SystemService = Depends(get_system_service)
):
    """Get settings by category."""
    try:
        settings = await service.get_settings_by_category(category)
        return [SystemSettingResponse.model_validate(setting) for setting in settings]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Backup type specific endpoints
@router.get("/backups/types/{backup_type}", response_model=List[SystemBackupResponse])
async def get_backups_by_type(
    backup_type: BackupType,
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return"),
    service: SystemService = Depends(get_system_service)
):
    """Get backups by type."""
    try:
        backups = await service.get_backups(
            backup_type=backup_type,
            limit=limit
        )
        return [SystemBackupResponse.model_validate(backup) for backup in backups]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/backups/status/{backup_status}", response_model=List[SystemBackupResponse])
async def get_backups_by_status(
    backup_status: BackupStatus,
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return"),
    service: SystemService = Depends(get_system_service)
):
    """Get backups by status."""
    try:
        backups = await service.get_backups(
            backup_status=backup_status,
            limit=limit
        )
        return [SystemBackupResponse.model_validate(backup) for backup in backups]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Health check endpoint
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for system management."""
    return {"status": "healthy", "service": "system-management"}