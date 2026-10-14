from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status
from ..models.user import UserDocument, UserRole
from ..models.project import ProjectDocument, ProjectStatus, utc_now_iso
from ..models.test_run import TestRunDocument, RunStatus
from ..schemas.test_run import RunCreate, RunStatusUpdate, ALLOWED_TRANSITIONS
from ..repositories.project_repository import ProjectRepository
from ..repositories.test_run_repository import TestRunRepository


class TestRunService:
    def __init__(
        self,
        test_run_repo: Optional[TestRunRepository] = None,
        project_repo: Optional[ProjectRepository] = None,
    ):
        self.test_run_repo = test_run_repo or TestRunRepository()
        self.project_repo = project_repo or ProjectRepository()

    async def _verify_project_ownership(self, project_id: str, current_user: UserDocument) -> ProjectDocument:
        project = await self.project_repo.find_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated project not found.",
            )
        if project.ownerId != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access this project's test runs.",
            )
        return project

    async def create_run(self, data: RunCreate, current_user: UserDocument) -> TestRunDocument:
        project = await self._verify_project_ownership(data.projectId, current_user)

        # 1. SSRF Validation
        from ..security.url_validator import is_safe_target_url
        is_safe, error_msg = is_safe_target_url(project.targetUrl)
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target URL security validation failed: {error_msg}",
            )

        # 2. Prevent concurrent duplicate runs for the same project
        active_runs = await self.test_run_repo.find_by_project_id(project.id, limit=5)
        for existing in active_runs:
            if existing.status in (RunStatus.RUNNING, RunStatus.PENDING):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A test run is already currently in progress for this project.",
                )

        now = utc_now_iso()
        initial_log = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": now,
            "level": "info",
            "message": f"Test run queued for project: {project.name}",
            "agent": "TestMaster-v3",
        }

        new_run = TestRunDocument(
            projectId=project.id,
            status=RunStatus.RUNNING,
            agent="TestMaster-v3",
            currentStage="Queued",
            stepsCompleted=1,
            totalSteps=9,
            logs=[initial_log],
            startTime=now,
        )

        created_run = await self.test_run_repo.create(new_run)

        # Update project metrics
        await self.project_repo.update(
            project.id,
            {
                "totalRuns": project.totalRuns + 1,
                "lastRunAt": now,
                "status": ProjectStatus.RUNNING,
            },
        )

        # 3. Trigger asynchronous background pipeline execution
        import os
        import asyncio
        from ..pipeline.runner import execute_pipeline_for_run
        if not os.environ.get("PYTEST_CURRENT_TEST") or getattr(self, "enable_background_pipeline", False):
            asyncio.create_task(
                execute_pipeline_for_run(
                    created_run.id,
                    project.id,
                    test_run_repo=self.test_run_repo,
                    project_repo=self.project_repo,
                )
            )

        return created_run

    async def get_run(self, run_id: str, current_user: UserDocument) -> TestRunDocument:
        run = await self.test_run_repo.find_by_id(run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test run not found.",
            )
        await self._verify_project_ownership(run.projectId, current_user)
        return run

    async def list_runs(
        self,
        project_id: Optional[str],
        current_user: UserDocument,
        limit: int = 50,
    ) -> List[TestRunDocument]:
        if project_id:
            await self._verify_project_ownership(project_id, current_user)
            return await self.test_run_repo.find_by_project_id(project_id, limit=limit)

        # List runs across all projects owned by the user
        if current_user.role == UserRole.ADMIN:
            return await self.test_run_repo.find_all(limit=limit)

        user_projects = await self.project_repo.find_by_owner_id(current_user.id)
        if not user_projects:
            return []

        project_ids = [p.id for p in user_projects]
        return await self.test_run_repo.find_by_project_ids(project_ids, limit=limit)

    async def update_run_status(
        self,
        run_id: str,
        data: RunStatusUpdate,
        current_user: UserDocument,
    ) -> TestRunDocument:
        run = await self.get_run(run_id, current_user)

        # Check allowed lifecycle transitions
        allowed = ALLOWED_TRANSITIONS.get(run.status, [])
        if data.status != run.status and data.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from '{run.status}' to '{data.status}'.",
            )

        now = utc_now_iso()
        updates: Dict[str, Any] = {"status": data.status}

        if data.stepsCompleted is not None:
            updates["stepsCompleted"] = data.stepsCompleted
        if data.errorTrace is not None:
            updates["errorTrace"] = data.errorTrace
        if data.report is not None:
            updates["report"] = data.report
        if data.metrics is not None:
            updates["metrics"] = data.metrics

        # Compute completion metrics on terminal states
        if data.status in (RunStatus.COMPLETED, RunStatus.FAILED) and not run.endTime:
            updates["endTime"] = now
            try:
                start_dt = datetime.fromisoformat(run.startTime)
                end_dt = datetime.fromisoformat(now)
                updates["duration"] = int((end_dt - start_dt).total_seconds())
            except Exception:
                updates["duration"] = 0

            # Update project status
            proj_status = ProjectStatus.COMPLETED if data.status == RunStatus.COMPLETED else ProjectStatus.FAILED
            await self.project_repo.update(run.projectId, {"status": proj_status})

        updated = await self.test_run_repo.update(run_id, updates)
        return updated or run

    async def cancel_run(self, run_id: str, current_user: UserDocument) -> bool:
        run = await self.get_run(run_id, current_user)
        if run.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
            return True  # Already finished

        from ..pipeline.runner import request_cancellation
        request_cancellation(run_id)

        now = utc_now_iso()
        cancel_log = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": now,
            "level": "warning",
            "message": "Test run cancelled by user.",
            "agent": "TestMaster-v3",
        }
        logs = list(run.logs) + [cancel_log]

        duration = 0
        try:
            start_dt = datetime.fromisoformat(run.startTime)
            end_dt = datetime.fromisoformat(now)
            duration = int((end_dt - start_dt).total_seconds())
        except Exception:
            pass

        await self.test_run_repo.update(
            run_id,
            {
                "status": RunStatus.FAILED,
                "cancelled": True,
                "endTime": now,
                "duration": duration,
                "errorTrace": "Cancelled by user.",
                "logs": logs,
            },
        )
        await self.project_repo.update(run.projectId, {"status": ProjectStatus.FAILED})
        return True

    async def restart_run(self, run_id: str, current_user: UserDocument) -> TestRunDocument:
        run = await self.get_run(run_id, current_user)
        return await self.create_run(RunCreate(projectId=run.projectId), current_user)


async def reconcile_interrupted_runs(
    test_run_repo: Optional[TestRunRepository] = None,
    project_repo: Optional[ProjectRepository] = None,
) -> int:
    """
    On backend startup, finds runs left in RUNNING or PENDING from a prior server instance,
    safely transitions them to FAILED with transparent diagnostic explanation, and reconciles project status.
    """
    test_run_repo = test_run_repo or TestRunRepository()
    project_repo = project_repo or ProjectRepository()

    interrupted = await test_run_repo.find_by_statuses([RunStatus.RUNNING.value, RunStatus.PENDING.value])
    if not interrupted:
        return 0

    reconciled_count = 0
    now = utc_now_iso()
    for run in interrupted:
        rec_log = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": now,
            "level": "warning",
            "message": "Backend server restarted while run was in progress. Interrupted run safely reconciled.",
            "agent": "TestMaster-v3",
        }
        updated_logs = list(run.logs) + [rec_log]
        await test_run_repo.update(
            run.id,
            {
                "status": RunStatus.FAILED,
                "endTime": now,
                "errorTrace": "Server was interrupted or restarted during execution. Run marked failed safely.",
                "logs": updated_logs,
            },
        )
        if run.projectId:
            proj = await project_repo.find_by_id(run.projectId)
            if proj and proj.status == ProjectStatus.RUNNING:
                await project_repo.update(proj.id, {"status": ProjectStatus.FAILED})
        reconciled_count += 1

    return reconciled_count
