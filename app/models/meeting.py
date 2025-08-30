from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid

from .database import Base

if TYPE_CHECKING:
    from .user import User

class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    UPLOADED = "uploaded"
    JOINING = "joining"
    ACTIVE = "active"
    TRANSCRIBING = "transcribing"
    TRANSCRIBED = "transcribed"
    SUMMARIZED = "summarized"
    COMPLETED = "completed"
    FAILED = "failed"

class MeetingPlatform(str, Enum):
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    MICROSOFT_TEAMS = "microsoft_teams"
    MANUAL_UPLOAD = "manual_upload"

class Meeting(Base):
    __tablename__ = "meetings"
    
    # Use consistent style - choose either all Column or all Mapped
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Meeting details
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    platform_meeting_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meeting_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Timing
    scheduled_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status and metadata
    status: Mapped[str] = mapped_column(String(50), default=MeetingStatus.UPLOADED.value)
    audio_file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    meeting_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # AI Processing results
    transcription_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    key_points: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sentiment_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Word counts and stats
    word_count_transcription: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    word_count_summary: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    participant_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Processing status
    transcription_status: Mapped[str] = mapped_column(String(50), default="pending")
    summary_status: Mapped[str] = mapped_column(String(50), default="pending")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - use consistent style
    user: Mapped["User"] = relationship("User", back_populates="meetings")
    participants: Mapped[List["MeetingParticipant"]] = relationship(
        "MeetingParticipant", back_populates="meeting", cascade="all, delete-orphan"
    )
    # Consider removing one of these if you don't need both
    transcripts: Mapped[List["MeetingTranscript"]] = relationship(
        "MeetingTranscript", back_populates="meeting", cascade="all, delete-orphan"
    )
    summaries: Mapped[List["MeetingSummary"]] = relationship(
        "MeetingSummary", back_populates="meeting", cascade="all, delete-orphan"
    )

class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meeting_id: Mapped[str] = mapped_column(String(36), ForeignKey("meetings.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    join_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    leave_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_host: Mapped[bool] = mapped_column(Boolean, default=False)
    is_agent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="participants")

class MeetingTranscript(Base):
    __tablename__ = "meeting_transcripts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meeting_id: Mapped[str] = mapped_column(String(36), ForeignKey("meetings.id"), nullable=False)
    
    speaker_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    speaker_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="transcripts")

class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meeting_id: Mapped[str] = mapped_column(String(36), ForeignKey("meetings.id"), nullable=False)
    
    summary_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="summaries")