from typing import List
from fastapi import APIRouter, Depends, status
from ..models.user import UserDocument
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from ..services.project_service import ProjectService
from ..security.dependencies import get_current_user


router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_project_service() -> ProjectService:
    return ProjectService()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: UserDocument = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    projects = await service.list_projects(current_user)
    return [ProjectResponse(**p.model_dump()) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: UserDocument = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    project = await service.create_project(payload, current_user)
    return ProjectResponse(**project.model_dump())


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: UserDocument = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    project = await service.get_project(project_id, current_user)
    return ProjectResponse(**project.model_dump())


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    current_user: UserDocument = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    updated = await service.update_project(project_id, payload, current_user)
    return ProjectResponse(**updated.model_dump())


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: UserDocument = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    success = await service.delete_project(project_id, current_user)
    return {"success": success}
