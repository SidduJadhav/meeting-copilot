# routes/user_settings.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import os

from app.models.user import User
from app.models.database import get_db
from app.services.oauth_service import current_active_user

# Change router variable name to avoid conflict
router = APIRouter(prefix="/settings", tags=["User Settings"])

@router.post("/recording-path")
async def set_recording_path(
    path: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set the user's Zoom recordings folder path
    """
    # Basic validation
    if not path or not path.strip():
        raise HTTPException(status_code=400, detail="Path cannot be empty")
    
    # Check if path exists
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Path does not exist")
    
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Path must be a directory")
    
    user.zoom_recordings_path = path.strip()
    user.last_folder_scan = datetime.utcnow()
    await db.commit()
    
    return {
        "message": "Recording path updated successfully",
        "path": user.zoom_recordings_path
    }

@router.get("/recording-path")
async def get_recording_path(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the user's configured Zoom recordings folder path
    """
    return {
        "recording_path": user.zoom_recordings_path,
        "last_scan": user.last_folder_scan
    }