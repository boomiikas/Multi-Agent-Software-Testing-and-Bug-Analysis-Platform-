from typing import Dict, Any, List, Optional
from ..models.user import UserDocument, UserRole
from ..models.project import ProjectDocument
from ..models.test_run import TestRunDocument, RunStatus
from ..repositories.project_repository import ProjectRepository
from ..repositories.test_run_repository import TestRunRepository


class DashboardService:
    def __init__(
        self,
        project_repo: Optional[ProjectRepository] = None,
        test_run_repo: Optional[TestRunRepository] = None,
    ):
        self.project_repo = project_repo or ProjectRepository()
        self.test_run_repo = test_run_repo or TestRunRepository()

    async def get_stats(self, current_user: UserDocument) -> Dict[str, Any]:
        if current_user.role == UserRole.ADMIN:
            projects = await self.project_repo.find_all()
            runs = await self.test_run_repo.find_all(limit=200)
        else:
            projects = await self.project_repo.find_by_owner_id(current_user.id)
            project_ids = [p.id for p in projects]
            runs = await self.test_run_repo.find_by_project_ids(project_ids, limit=200) if project_ids else []

        total_projects = len(projects)
        active_runs = sum(1 for r in runs if r.status == RunStatus.RUNNING)
        completed_runs = sum(1 for r in runs if r.status == RunStatus.COMPLETED)
        failed_runs = sum(1 for r in runs if r.status == RunStatus.FAILED)
        total_finished = completed_runs + failed_runs

        pass_rate = round((completed_runs / total_finished * 100), 1) if total_finished > 0 else 0.0

        durations = [r.duration for r in runs if r.duration is not None and r.duration > 0]
        if durations:
            avg_sec = int(sum(durations) / len(durations))
            m = avg_sec // 60
            s = avg_sec % 60
            avg_duration_str = f"{m}m {s}s"
        else:
            avg_duration_str = "0m 0s"

        return {
            "totalProjects": total_projects,
            "activeRuns": active_runs,
            "passRate": pass_rate,
            "avgDuration": avg_duration_str,
            "totalProjectsTrend": 0.0,
            "activeRunsTrend": 0.0,
            "passRateTrend": 0.0,
            "avgDurationTrend": 0.0,
        }

    async def get_recent_runs(self, current_user: UserDocument, limit: int = 10) -> List[Dict[str, Any]]:
        if current_user.role == UserRole.ADMIN:
            projects = await self.project_repo.find_all()
            runs = await self.test_run_repo.find_all(limit=limit)
        else:
            projects = await self.project_repo.find_by_owner_id(current_user.id)
            project_ids = [p.id for p in projects]
            runs = await self.test_run_repo.find_by_project_ids(project_ids, limit=limit) if project_ids else []

        project_map = {p.id: p.name for p in projects}

        results = []
        for r in runs:
            r_dict = r.model_dump()
            r_dict["projectName"] = project_map.get(r.projectId, "Unknown Project")
            r_dict["runId"] = r.id
            results.append(r_dict)

        return results
