from routes.auth import router as auth_router
from routes.complaints import router as complaints_router
from routes.departments import router as departments_router
from routes.users import router as users_router

__all__ = ["auth_router", "complaints_router", "departments_router", "users_router"]
