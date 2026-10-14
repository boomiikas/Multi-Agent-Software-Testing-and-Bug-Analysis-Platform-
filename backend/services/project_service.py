from typing import List, Optional
from fastapi import HTTPException, status
from ..models.user import UserDocument, UserRole
from ..models.project import ProjectDocument, ProjectStatus
from ..schemas.project import ProjectCreate, ProjectUpdate
from ..repositories.project_repository import ProjectRepository
from ..repositories.test_run_repository import TestRunRepository


class ProjectService:
    def __init__(
        self,
        project_repo: Optional[ProjectRepository] = None,
        test_run_repo: Optional[TestRunRepository] = None,
    ):
        self.project_repo = project_repo or ProjectRepository()
        self.test_run_repo = test_run_repo or TestRunRepository()

    async def list_projects(self, current_user: UserDocument) -> List[ProjectDocument]:
        # Return projects owned by current user (or all if admin requested)
        if current_user.role == UserRole.ADMIN:
            # Admins can see all projects or their own; returning their own plus unassigned or all
            projects = await self.project_repo.find_all()
        else:
            projects = await self.project_repo.find_by_owner_id(current_user.id)
        return projects

    async def get_project(self, project_id: str, current_user: UserDocument) -> ProjectDocument:
        project = await self.project_repo.find_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )
        
        # Enforce ownership check
        if project.ownerId != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access this project.",
            )
            
        return project

    async def create_project(self, data: ProjectCreate, current_user: UserDocument) -> ProjectDocument:
        srs = data.get_srs_content()
        new_project = ProjectDocument(
            name=data.name,
            targetUrl=data.targetUrl,
            srsDocument=srs,
            markdownSRS=srs,
            ownerId=current_user.id,
            status=ProjectStatus.PENDING,
            totalRuns=0,
            passRate=0.0,
        )
        return await self.project_repo.create(new_project)

    async def update_project(
        self,
        project_id: str,
        data: ProjectUpdate,
        current_user: UserDocument,
    ) -> ProjectDocument:
        # Check existence and ownership
        project = await self.get_project(project_id, current_user)
        
        updates = {}
        if data.name is not None:
            updates["name"] = data.name
        if data.targetUrl is not None:
            updates["targetUrl"] = data.targetUrl
        if data.srsDocument is not None:
            updates["srsDocument"] = data.srsDocument
            updates["markdownSRS"] = data.srsDocument
        elif data.markdownSRS is not None:
            updates["srsDocument"] = data.markdownSRS
            updates["markdownSRS"] = data.markdownSRS
        if data.status is not None:
            updates["status"] = data.status

        if not updates:
            return project

        updated = await self.project_repo.update(project_id, updates)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )
        return updated

    async def delete_project(self, project_id: str, current_user: UserDocument) -> bool:
        # Check existence and ownership
        await self.get_project(project_id, current_user)
        
        # Cascade cleanup: remove test runs associated with project
        await self.test_run_repo.delete_by_project_id(project_id)
        
        # Delete project record
        success = await self.project_repo.delete(project_id)
        return success
