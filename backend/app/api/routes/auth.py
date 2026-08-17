from typing import Dict, Any
from fastapi import APIRouter, Depends
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    """Return currently active user identity and role."""
    return user

@router.get("/roles")
async def get_available_roles():
    """Return available roles in the system."""
    return [
        {
            "role": "admin",
            "name": "Administrator",
            "description": "Full access to CRUD operations and publishing to production catalogue."
        },
        {
            "role": "editor",
            "name": "Content Editor",
            "description": "Access to view/edit content, upload artwork, and review validation reports. Cannot publish."
        }
    ]
