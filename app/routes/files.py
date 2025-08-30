import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Dict, Any

from app.models.user import User
from app.models.database import get_db
from app.services.oauth_service import current_active_user

router = APIRouter(prefix="/files", tags=["Files"])

@router.get("/list")
async def list_recordings(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List audio/video files from user's configured recordings folder
    """
    if not user.zoom_recordings_path:
        raise HTTPException(status_code=400, detail="No recording path configured")
    
    if not os.path.exists(user.zoom_recordings_path):
        raise HTTPException(status_code=404, detail="Recording path not found")
    
    files = []
    valid_extensions = ('.mp3', '.mp4', '.wav', '.m4a', '.mov', '.avi')
    
    try:
        for filename in os.listdir(user.zoom_recordings_path):
            file_path = os.path.join(user.zoom_recordings_path, filename)
            if (os.path.isfile(file_path) and 
                filename.lower().endswith(valid_extensions)):
                
                files.append({
                    "name": filename,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)),
                    "path": file_path
                })
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied accessing folder")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading folder: {str(e)}")
    
    return {"files": sorted(files, key=lambda x: x["modified"], reverse=True)}