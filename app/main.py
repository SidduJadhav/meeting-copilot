from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

from app.routes import auth, meetings, files, user_settings 
from app.models.database import database    
from app.config import settings  # Make sure this import exists



# Create uploads directory if it doesn't exist
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Meeting Copilot API",
    description="AI-powered meeting transcription and summarization with user authentication",
    version="1.0.0"
)
# Add this temporarily to your main.py to debug:
print(f"Database URL: {settings.DATABASE_URL}")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers - Authentication routes first
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(meetings.router, prefix="/api", tags=["meetings"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(user_settings.router, prefix="/api", tags=["settings"])

# Database startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and start auto upload watcher"""
    print("Starting Meeting Copilot API...")
    
    # Connect to database
    await database.connect()
    await database.create_all()
    print("Database initialized successfully")
    
    # Start the auto-upload watcher if enabled
   
    
    print("Meeting Copilot API is ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await database.disconnect()
    print("Database disconnected")

@app.get("/")
async def read_root(request: Request):
    """Serve the main page (redirects to appropriate page based on auth)"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/meeting/{meeting_id}")
async def meeting_page(request: Request, meeting_id: str):
    """Serve the meeting page with WebSocket support"""
    return templates.TemplateResponse("meeting.html", {
        "request": request, 
        "meeting_id": meeting_id
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "authentication": "enabled",
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "groq_configured": bool(settings.GROQ_API_KEY),
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG  # Only reload in debug mode
    )