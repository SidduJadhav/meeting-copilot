import os
import json
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import mimetypes

from app.config import settings

async def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file"""
    # Check file size
    if hasattr(file, 'size') and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )
    
    # Check file extension
    if file.filename:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
    
    # Check content type
    if file.content_type:
        allowed_types = [
            "audio/", "video/", "text/", 
            "application/octet-stream"  # For some audio files
        ]
        if not any(file.content_type.startswith(t) for t in allowed_types):
            raise HTTPException(
                status_code=400,
                detail=f"Content type not supported: {file.content_type}"
            )
    
    return True

async def save_uploaded_file(file: UploadFile, meeting_id: str) -> Path:
    """Save uploaded file to disk"""
    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = Path(settings.UPLOAD_DIR)
        uploads_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix if file.filename else ""
        filename = f"{meeting_id}{file_ext}"
        file_path = uploads_dir / filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

async def load_meeting_data(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Load meeting metadata from JSON file"""
    try:
        metadata_file = Path(settings.UPLOAD_DIR) / f"{meeting_id}_metadata.json"
        
        if not metadata_file.exists():
            return None
        
        async with aiofiles.open(metadata_file, 'r') as f:
            content = await f.read()
            return json.loads(content)
            
    except Exception as e:
        print(f"Error loading meeting data: {e}")
        return None

async def save_meeting_data(meeting_id: str, data: Dict[str, Any]) -> bool:
    """Save meeting metadata to JSON file"""
    try:
        # Add timestamps
        if not data.get("created_at"):
            data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        
        metadata_file = Path(settings.UPLOAD_DIR) / f"{meeting_id}_metadata.json"
        
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(data, indent=2))
        
        return True
        
    except Exception as e:
        print(f"Error saving meeting data: {e}")
        return False

def get_file_type(filename: str) -> str:
    """Determine file type from filename"""
    if not filename:
        return "unknown"
    
    mime_type, _ = mimetypes.guess_type(filename)
    
    if mime_type:
        if mime_type.startswith("audio/"):
            return "audio"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("text/"):
            return "text"
    
    # Fallback to extension
    ext = Path(filename).suffix.lower()
    
    audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
    video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".wmv"}
    text_exts = {".txt", ".md", ".doc", ".docx", ".pdf"}
    
    if ext in audio_exts:
        return "audio"
    elif ext in video_exts:
        return "video"
    elif ext in text_exts:
        return "text"
    
    return "unknown"

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def estimate_processing_time(file_size_bytes: int, file_type: str) -> str:
    """Estimate processing time based on file size and type"""
    size_mb = file_size_bytes / (1024 * 1024)
    
    if file_type == "text":
        return "< 10 seconds"
    elif file_type == "audio":
        # Roughly 1MB per minute of audio
        estimated_minutes = size_mb
        processing_time = estimated_minutes * 0.1  # 10% of duration for transcription
        return f"~{max(1, int(processing_time))} minute(s)"
    elif file_type == "video":
        # Video files are larger but same transcription time as audio
        estimated_minutes = size_mb / 10  # Rough estimate
        processing_time = estimated_minutes * 0.1
        return f"~{max(1, int(processing_time))} minute(s)"
    
    return "Unknown"

async def cleanup_old_files(days_old: int = 7) -> int:
    """Clean up files older than specified days"""
    try:
        uploads_dir = Path(settings.UPLOAD_DIR)
        if not uploads_dir.exists():
            return 0
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        cleaned_count = 0
        
        for file_path in uploads_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned_count += 1
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        
        return cleaned_count
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 0

def generate_meeting_id() -> str:
    """Generate a unique meeting ID"""
    return str(uuid.uuid4())

async def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get detailed file information"""
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        
        return {
            "filename": path.name,
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix,
            "type": get_file_type(path.name)
        }
        
    except Exception as e:
        return {"error": str(e)}
