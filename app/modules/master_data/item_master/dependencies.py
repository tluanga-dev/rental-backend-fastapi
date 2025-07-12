from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.master_data.item_master.service import ItemMasterService
from app.modules.master_data.item_master.repository import ItemMasterRepository


def get_item_master_repository(session: AsyncSession = Depends(get_session)) -> ItemMasterRepository:
    """Get item master repository instance."""
    return ItemMasterRepository(session)


def get_item_master_service(session: AsyncSession = Depends(get_session)) -> ItemMasterService:
    """Get item master service instance."""
    return ItemMasterService(session)