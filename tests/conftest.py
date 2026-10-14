import pytest
from typing import Optional, List
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.user import UserDocument, ResetTokenDocument, UserRole, utc_now_iso
from backend.models.project import ProjectDocument, ProjectStatus
from backend.models.test_run import TestRunDocument, RunStatus
from backend.repositories.user_repository import UserRepository, get_user_repository
from backend.repositories.project_repository import ProjectRepository, get_project_repository
from backend.repositories.test_run_repository import TestRunRepository, get_test_run_repository
from backend.services.project_service import ProjectService
from backend.services.test_run_service import TestRunService
from backend.services.dashboard_service import DashboardService
from backend.routers.projects import get_project_service
from backend.routers.test_runs import get_test_run_service
from backend.routers.dashboard import get_dashboard_service
from backend.security.passwords import hash_password
from backend.security.tokens import sign_auth_token


class InMemoryUserRepository(UserRepository):
    """Isolated, zero-dependency in-memory user repository for automated testing."""
    def __init__(self):
        super().__init__(db=None)
        self.users: dict[str, UserDocument] = {}
        self.reset_tokens: dict[str, ResetTokenDocument] = {}

    async def find_all(self) -> List[UserDocument]:
        return list(self.users.values())

    async def find_by_id(self, user_id: str) -> Optional[UserDocument]:
        return self.users.get(user_id)

    async def find_by_email(self, email: str) -> Optional[UserDocument]:
        for u in self.users.values():
            if u.email.lower() == email.lower():
                return u
        return None

    async def create(self, user: UserDocument) -> UserDocument:
        self.users[user.id] = user
        return user

    async def update(self, user_id: str, updates: dict) -> Optional[UserDocument]:
        user = self.users.get(user_id)
        if not user:
            return None
        data = user.model_dump()
        data.update(updates)
        data["updatedAt"] = utc_now_iso()
        updated = UserDocument(**data)
        self.users[user_id] = updated
        return updated

    async def delete(self, user_id: str) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False

    async def save_reset_token(self, user_id: str, token_hash: str, expires_at: float):
        self.reset_tokens = {k: v for k, v in self.reset_tokens.items() if v.userId != user_id}
        self.reset_tokens[token_hash] = ResetTokenDocument(
            userId=user_id,
            tokenHash=token_hash,
            expiresAt=expires_at,
        )

    async def find_reset_token(self, token_hash: str) -> Optional[ResetTokenDocument]:
        return self.reset_tokens.get(token_hash)

    async def delete_reset_token(self, token_hash: str):
        self.reset_tokens.pop(token_hash, None)


class InMemoryProjectRepository(ProjectRepository):
    """Isolated, in-memory project repository for testing."""
    def __init__(self):
        super().__init__(db=None)
        self.projects: dict[str, ProjectDocument] = {}

    async def find_all(self) -> List[ProjectDocument]:
        return list(self.projects.values())

    async def find_by_owner_id(self, owner_id: str) -> List[ProjectDocument]:
        return [p for p in self.projects.values() if p.ownerId == owner_id]

    async def find_by_id(self, project_id: str) -> Optional[ProjectDocument]:
        return self.projects.get(project_id)

    async def create(self, project: ProjectDocument) -> ProjectDocument:
        self.projects[project.id] = project
        return project

    async def update(self, project_id: str, updates: dict) -> Optional[ProjectDocument]:
        proj = self.projects.get(project_id)
        if not proj:
            return None
        data = proj.model_dump()
        data.update(updates)
        data["updatedAt"] = utc_now_iso()
        updated = ProjectDocument(**data)
        self.projects[project_id] = updated
        return updated

    async def delete(self, project_id: str) -> bool:
        if project_id in self.projects:
            del self.projects[project_id]
            return True
        return False


class InMemoryTestRunRepository(TestRunRepository):
    """Isolated, in-memory test run repository for testing."""
    def __init__(self):
        super().__init__(db=None)
        self.runs: dict[str, TestRunDocument] = {}

    async def find_all(self, limit: int = 50) -> List[TestRunDocument]:
        return list(self.runs.values())[:limit]

    async def find_by_id(self, run_id: str) -> Optional[TestRunDocument]:
        return self.runs.get(run_id)

    async def find_by_project_id(self, project_id: str, limit: int = 50) -> List[TestRunDocument]:
        return [r for r in self.runs.values() if r.projectId == project_id][:limit]

    async def find_by_project_ids(self, project_ids: List[str], limit: int = 50) -> List[TestRunDocument]:
        return [r for r in self.runs.values() if r.projectId in project_ids][:limit]

    async def find_by_statuses(self, statuses: List[str]) -> List[TestRunDocument]:
        return [r for r in self.runs.values() if r.status in statuses]

    async def create(self, run: TestRunDocument) -> TestRunDocument:
        self.runs[run.id] = run
        return run

    async def update(self, run_id: str, updates: dict) -> Optional[TestRunDocument]:
        run = self.runs.get(run_id)
        if not run:
            return None
        data = run.model_dump()
        data.update(updates)
        updated = TestRunDocument(**data)
        self.runs[run_id] = updated
        return updated

    async def delete(self, run_id: str) -> bool:
        if run_id in self.runs:
            del self.runs[run_id]
            return True
        return False

    async def delete_by_project_id(self, project_id: str) -> int:
        to_del = [k for k, v in self.runs.items() if v.projectId == project_id]
        for k in to_del:
            del self.runs[k]
        return len(to_del)


async def _async_noop(*args, **kwargs):
    pass


@pytest.fixture(autouse=True)
def prevent_lifespan_cloud_mongo(monkeypatch):
    monkeypatch.setattr("backend.main.connect_to_mongo", _async_noop)
    monkeypatch.setattr("backend.main.seed_admin", _async_noop)
    monkeypatch.setattr("backend.main.close_mongo_connection", _async_noop)


@pytest.fixture
def mock_user_repo():
    return InMemoryUserRepository()


@pytest.fixture
def mock_project_repo():
    return InMemoryProjectRepository()


@pytest.fixture
def mock_test_run_repo():
    return InMemoryTestRunRepository()


@pytest.fixture
def client(mock_user_repo, mock_project_repo, mock_test_run_repo):
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repo
    app.dependency_overrides[get_project_repository] = lambda: mock_project_repo
    app.dependency_overrides[get_test_run_repository] = lambda: mock_test_run_repo

    project_svc = ProjectService(project_repo=mock_project_repo, test_run_repo=mock_test_run_repo)
    test_run_svc = TestRunService(test_run_repo=mock_test_run_repo, project_repo=mock_project_repo)
    dashboard_svc = DashboardService(project_repo=mock_project_repo, test_run_repo=mock_test_run_repo)

    app.dependency_overrides[get_project_service] = lambda: project_svc
    app.dependency_overrides[get_test_run_service] = lambda: test_run_svc
    app.dependency_overrides[get_dashboard_service] = lambda: dashboard_svc

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def standard_user(mock_user_repo):
    user = UserDocument(
        id="usr-test-123",
        fullName="Test User",
        email="test@example.com",
        password=hash_password("UserPass123"),
        role=UserRole.USER,
    )
    mock_user_repo.users[user.id] = user
    return user


@pytest.fixture
def other_user(mock_user_repo):
    user = UserDocument(
        id="usr-other-456",
        fullName="Other User",
        email="other@example.com",
        password=hash_password("OtherPass123"),
        role=UserRole.USER,
    )
    mock_user_repo.users[user.id] = user
    return user


@pytest.fixture
def admin_user(mock_user_repo):
    admin = UserDocument(
        id="admin-test-999",
        fullName="Admin User",
        email="admin@example.com",
        password=hash_password("AdminPass123"),
        role=UserRole.ADMIN,
    )
    mock_user_repo.users[admin.id] = admin
    return admin


@pytest.fixture
def user_auth_headers(standard_user):
    token = sign_auth_token(standard_user.id, standard_user.email, standard_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_auth_headers(other_user):
    token = sign_auth_token(other_user.id, other_user.email, other_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(admin_user):
    token = sign_auth_token(admin_user.id, admin_user.email, admin_user.role.value)
    return {"Authorization": f"Bearer {token}"}
