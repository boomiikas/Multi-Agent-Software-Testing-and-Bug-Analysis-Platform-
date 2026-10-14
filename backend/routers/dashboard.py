from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from ..models.user import UserDocument
from ..services.dashboard_service import DashboardService
from ..security.dependencies import get_current_user


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_dashboard_service() -> DashboardService:
    return DashboardService()


@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    current_user: UserDocument = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_stats(current_user)


@router.get("/runs", response_model=List[Dict[str, Any]])
async def get_dashboard_runs(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserDocument = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_recent_runs(current_user, limit=limit)
