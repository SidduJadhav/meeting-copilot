from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String , DateTime
from app.models.database import Base
from typing import TYPE_CHECKING, Optional
from datetime import datetime


if TYPE_CHECKING:
    from .meeting import Meeting

class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    
    # Add full_name field
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="User's full name"
    )
    
    # Optional: Add other custom fields you might need
    # company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationship to meetings
    meetings: Mapped[list["Meeting"]] = relationship(
        "Meeting", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="selectin"  # Optional: controls how relationships are loaded
    )

    zoom_recordings_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_folder_scan: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.email}>"