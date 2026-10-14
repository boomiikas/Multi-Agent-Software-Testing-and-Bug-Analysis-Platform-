from .auth import router as auth_router
from .users import router as users_router
from .admin import router as admin_router
from .projects import router as projects_router
from .test_runs import router as test_runs_router
from .dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "users_router",
    "admin_router",
    "projects_router",
    "test_runs_router",
    "dashboard_router",
]

