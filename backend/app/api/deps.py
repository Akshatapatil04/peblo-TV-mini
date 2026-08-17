from typing import List, Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.core.config import settings

def get_current_user(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Authenticate and extract user role.
    Supports:
    1. Header `X-User-Role`: 'admin' | 'editor'
    2. Header `Authorization: Bearer <role_or_key>`
    Defaults to 'admin' in development if no header provided, or 'editor'.
    """
    role = "editor"  # Safe default

    if x_user_role:
        role = x_user_role.strip().lower()
    elif authorization:
        token = authorization.replace("Bearer ", "").strip()
        if token == settings.ADMIN_API_KEY or token.lower() == "admin":
            role = "admin"
        elif token == settings.EDITOR_API_KEY or token.lower() == "editor":
            role = "editor"
        else:
            role = token.lower()

    # Normalize role
    if role not in ("admin", "editor", "viewer"):
        role = "editor"

    return {
        "id": f"usr_{role}",
        "role": role,
        "name": f"Peblo {role.capitalize()}",
        "email": f"{role}@peblo.tv"
    }

def require_role(allowed_roles: List[str]):
    """Enforces role-based access control (e.g. ['admin'])."""
    def _role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role", "viewer")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "message": f"Action requires one of the following roles: {', '.join(allowed_roles)}. Your current role is '{user_role}'.",
                    "current_role": user_role,
                    "required_roles": allowed_roles
                }
            )
        return user
    return _role_checker
