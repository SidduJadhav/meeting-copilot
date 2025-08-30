from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import shutil
import os
import uuid
from typing import Optional

from app.models.meeting import Meeting
from app.models.user import User
from app.models.database import get_db
from app.services.transcription import TranscriptionService
from app.services.summarization import SummarizationService
from app.services.oauth_service import current_active_user

router = APIRouter(prefix="/meetings", tags=["Meetings"])

# Configure upload folder   
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize services
transcription_service = TranscriptionService()
summarization_service = SummarizationService()

# 1. List User's Meetings
@router.get("/")
async def list_meetings(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all meetings for the current user"""
    result = await db.execute(
        select(Meeting)
        .filter(Meeting.user_id == user.id)
        .order_by(Meeting.created_at.desc())
    )
    meetings = result.scalars().all()
    return meetings

# 2. Upload Meeting
@router.post("/upload")
async def upload_meeting(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a meeting file for processing"""
    try:
        unique_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{unique_id}_{file.filename}")
        
        # Get title from form or use filename
        meeting_title = title if title and title.strip() else file.filename

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_meeting = Meeting(
            id=unique_id,
            user_id=user.id,
            title=meeting_title,
            platform="manual_upload",
            status="uploaded",
            audio_file_path=file_path,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_meeting)
        await db.commit()
        await db.refresh(new_meeting)
        
        return {
            "meeting_id": unique_id, 
            "message": "File uploaded successfully.",
            "title": meeting_title,
            "status": "uploaded"
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# 3. Transcribe Meeting
@router.post("/transcribe/{meeting_id}")
async def transcribe_meeting(
    meeting_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Transcribe a meeting's audio file"""
    result = await db.execute(
        select(Meeting).filter(
            Meeting.id == meeting_id,
            Meeting.user_id == user.id
        )
    )
    meeting = result.scalars().first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not os.path.exists(meeting.audio_file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    try:
        meeting.status = "transcribing"
        meeting.transcription_status = "processing"
        await db.commit()
        
        transcription = await transcription_service.transcribe_file(meeting.audio_file_path)
        
        meeting.transcription_text = transcription
        meeting.status = "transcribed"
        meeting.transcription_status = "completed"
        meeting.word_count_transcription = len(transcription.split()) if transcription else 0
        meeting.updated_at = datetime.utcnow()
        await db.commit()
        
        return {
            "meeting_id": meeting.id, 
            "transcription": transcription,
            "word_count": meeting.word_count_transcription,
            "status": "transcribed"
        }

    except Exception as e:
        await db.rollback()
        meeting.status = "failed"
        meeting.transcription_status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

# 4. Summarize Meeting
@router.post("/summarize/{meeting_id}")
async def summarize_meeting(
    meeting_id: str,
    style: str = "detailed",
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a summary of the meeting transcription"""
    result = await db.execute(
        select(Meeting).filter(
            Meeting.id == meeting_id,
            Meeting.user_id == user.id
        )
    )
    meeting = result.scalars().first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not meeting.transcription_text:
        raise HTTPException(status_code=400, detail="No transcription available. Please transcribe first.")

    try:
        meeting.summary_status = "processing"
        await db.commit()
        
        summary = await summarization_service.summarize_text(meeting.transcription_text, style)
        
        meeting.summary_text = summary
        meeting.status = "summarized"
        meeting.summary_status = "completed"
        meeting.word_count_summary = len(summary.split()) if summary else 0
        meeting.updated_at = datetime.utcnow()
        await db.commit()
        
        return {
            "meeting_id": meeting.id, 
            "summary": summary,
            "style": style,
            "word_count": meeting.word_count_summary,
            "status": "summarized"
        }

    except Exception as e:
        await db.rollback()
        meeting.summary_status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

# 5. Process Meeting (Transcribe + Summarize)
@router.post("/process/{meeting_id}")
async def process_meeting(
    meeting_id: str,
    style: str = "detailed",
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Process a meeting: transcribe and then summarize"""
    result = await db.execute(
        select(Meeting).filter(
            Meeting.id == meeting_id,
            Meeting.user_id == user.id
        )
    )
    meeting = result.scalars().first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not os.path.exists(meeting.audio_file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    try:
        # Update status to processing
        meeting.status = "transcribing"
        meeting.transcription_status = "processing"
        meeting.summary_status = "pending"
        await db.commit()
        
        # Transcribe
        transcription = await transcription_service.transcribe_file(meeting.audio_file_path)
        meeting.transcription_text = transcription
        meeting.transcription_status = "completed"
        meeting.word_count_transcription = len(transcription.split()) if transcription else 0
        
        # Update status for summarization
        meeting.status = "transcribed"
        meeting.summary_status = "processing"
        await db.commit()
        
        # Summarize
        summary = await summarization_service.summarize_text(transcription, style)
        meeting.summary_text = summary
        meeting.summary_status = "completed"
        meeting.word_count_summary = len(summary.split()) if summary else 0
        
        # Final status update
        meeting.status = "summarized"
        meeting.updated_at = datetime.utcnow()
        await db.commit()

        return {
            "meeting_id": meeting.id,
            "transcription": transcription,
            "summary": summary,
            "word_count_transcription": meeting.word_count_transcription,
            "word_count_summary": meeting.word_count_summary,
            "status": "summarized"
        }

    except Exception as e:
        await db.rollback()
        meeting.status = "failed"
        meeting.transcription_status = "failed" if not meeting.transcription_text else meeting.transcription_status
        meeting.summary_status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# 6. Get Meeting Details
@router.get("/{meeting_id}")
async def get_meeting(
    meeting_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific meeting"""
    result = await db.execute(
        select(Meeting).filter(
            Meeting.id == meeting_id,
            Meeting.user_id == user.id
        )
    )
    meeting = result.scalars().first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

# 7. Delete Meeting
@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a meeting and its associated file"""
    result = await db.execute(
        select(Meeting).filter(
            Meeting.id == meeting_id,
            Meeting.user_id == user.id
        )
    )
    meeting = result.scalars().first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    try:
        # Delete associated file if it exists
        if meeting.audio_file_path and os.path.exists(meeting.audio_file_path):
            os.unlink(meeting.audio_file_path)
        
        # Delete from database
        await db.delete(meeting)
        await db.commit()
        
        return {"message": "Meeting deleted successfully", "meeting_id": meeting_id}
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete meeting: {str(e)}")


# routes/meetings.py - modify upload endpoint
@router.post("/upload-from-path")
async def upload_from_path(
    file_path: str,
    title: Optional[str] = None,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file from user's local path"""
    # Security check: ensure file is in user's configured path
    if not file_path.startswith(user.zoom_recordings_path):
        raise HTTPException(403, "File not in authorized directory")
    
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    
    # Continue with existing upload logic...
    return await upload_meeting(file_path, title, user, db)
# 8. Get Meeting Statistics
@router.get("/stats/summary")
async def get_meeting_stats(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics about user's meetings"""
    result = await db.execute(
        select(Meeting).filter(Meeting.user_id == user.id)
    )
    meetings = result.scalars().all()
    
    total_meetings = len(meetings)
    transcribed_meetings = len([m for m in meetings if m.transcription_text])
    summarized_meetings = len([m for m in meetings if m.summary_text])
    total_duration = sum([m.duration_minutes or 0 for m in meetings])
    
    return {
        "total_meetings": total_meetings,
        "transcribed_meetings": transcribed_meetings,
        "summarized_meetings": summarized_meetings,
        "total_duration_minutes": total_duration,
        "avg_duration_minutes": total_duration / total_meetings if total_meetings > 0 else 0
    }