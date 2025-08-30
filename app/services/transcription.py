import os
import aiofiles
from openai import AsyncOpenAI
from pathlib import Path
from typing import Optional

from app.config import settings

class TranscriptionService:
    """Service for audio/video transcription using Groq's Whisper API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = settings.WHISPER_MODEL
    
    async def transcribe_file(self, file_path: str) -> str:
        """Transcribe audio/video file to text"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check file size (Groq has limits)
            file_size = file_path.stat().st_size
            max_size = 25 * 1024 * 1024  # 25MB limit for Groq
            
            if file_size > max_size:
                raise ValueError(f"File too large: {file_size / 1024 / 1024:.1f}MB. Maximum: 25MB")
            
            # Open and transcribe file
            with open(file_path, "rb") as audio_file:
                transcription = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    prompt="This is a meeting, interview, or podcast transcription. Include speakers and context.",
                    response_format="text",
                    temperature=0.0
                )
            
            return transcription
            
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
    
    async def transcribe_with_timestamps(self, file_path: str) -> dict:
        """Transcribe with timestamp information"""
        try:
            file_path = Path(file_path)
            
            with open(file_path, "rb") as audio_file:
                transcription = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                    temperature=0.0
                )
            
            return {
                "text": transcription.text,
                "segments": transcription.segments if hasattr(transcription, 'segments') else [],
                "duration": transcription.duration if hasattr(transcription, 'duration') else None,
                "words": transcription.words if hasattr(transcription, 'words') else []
            }
            
        except Exception as e:
            raise Exception(f"Transcription with timestamps failed: {str(e)}")
    
    async def transcribe_chunk(self, audio_chunk: bytes, format: str = "wav") -> str:
        """Transcribe audio chunk for real-time processing"""
        try:
            # Create temporary file for the chunk
            temp_file = f"/tmp/chunk_{os.urandom(8).hex()}.{format}"
            
            async with aiofiles.open(temp_file, 'wb') as f:
                await f.write(audio_chunk)
            
            # Transcribe the chunk
            transcription = await self.transcribe_file(temp_file)
            
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
            
            return transcription
            
        except Exception as e:
            raise Exception(f"Chunk transcription failed: {str(e)}")
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio/video formats"""
        return [
            ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", 
            ".wav", ".webm", ".mov", ".avi"
        ]
    
    async def validate_audio_file(self, file_path: str) -> bool:
        """Validate if file is supported for transcription"""
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                return False
            
            # Check file extension
            if file_path.suffix.lower() not in self.get_supported_formats():
                return False
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > 25 * 1024 * 1024:  # 25MB limit
                return False
            
            return True
            
        except Exception:
            return False
