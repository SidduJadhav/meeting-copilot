import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database
    #DATABASE_URL: str = "postgresql+asyncpg://meetinguser:meetingpassword123@localhost:5432/meetingcopilot"
    # In config.py, change to:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://meeting:1234@localhost:5432/meeting")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")

    # Authentication
    SECRET_KEY: Optional[str] = None
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    
    # OAuth Settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    ZOOM_CLIENT_ID: Optional[str] = None
    ZOOM_CLIENT_SECRET: Optional[str] = None
    
    # Auto Upload Settings
    AUTO_UPLOAD_USER_EMAIL: str = "auto-upload@meetingcopilot.ai"
    AUTO_UPLOAD_USER_PASSWORD: str = "auto-upload-password-123"
    AUTO_UPLOAD_ENABLED: bool = True
    
    # Meeting Agent Settings
    AGENT_NAME: str = "AI Meeting Assistant"
    AGENT_EMAIL: str = "ai-assistant@meetingcopilot.ai"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    ALLOWED_EXTENSIONS: set = {".mp3", ".wav", ".m4a", ".mp4", ".mov", ".avi", ".txt"}
    UPLOAD_DIR: str = "uploads"
    
    # AI Model Settings
    GEMINI_MODEL: str = "gemini-2.5-flash"
    WHISPER_MODEL: str = "whisper-large-v3"
    
    # Summary Settings
    DEFAULT_SUMMARY_LENGTH: str = "detailed"
    MAX_SUMMARY_TOKENS: int = 1000
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # Redis settings for Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Meeting settings
    MAX_MEETING_DURATION_HOURS: int = 8
    TRANSCRIPTION_CHUNK_DURATION: int = 30
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env" if os.getenv("ENVIRONMENT") != "production" else None
        case_sensitive = True
        extra = "ignore"

# If you need constants that aren't settings, define them outside the class
API_BASE_URL: str = "http://localhost:8000"  # Outside the class

settings = Settings()

def validate_api_keys():
    """Validate that required API keys are present"""
    missing_keys = []
    
    if not settings.GEMINI_API_KEY:
        missing_keys.append("GEMINI_API_KEY")
    
    if not settings.GROQ_API_KEY:
        missing_keys.append("GROQ_API_KEY")
    
    if missing_keys:
        print(f"Warning: Missing required API keys: {', '.join(missing_keys)}")
        print("Some features may not work without proper API keys.")
    
    # Generate SECRET_KEY if not provided
    if not settings.SECRET_KEY:
        import secrets
        generated_key = secrets.token_urlsafe(32)
        print(f"Warning: No SECRET_KEY provided. Using generated key for this session.")
        print(f"For production, set SECRET_KEY in your .env file: SECRET_KEY={generated_key}")
        settings.SECRET_KEY = generated_key

validate_api_keys()