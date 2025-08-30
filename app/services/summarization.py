import os
import json
from google import genai
from google.genai import types
from typing import Dict, Any, Optional

from app.config import settings

class SummarizationService:
    """Service for AI-powered summarization using Google Gemini"""
    
    def __init__(self):
        self.client = None
        self.model = settings.GEMINI_MODEL
        if settings.GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception:
                self.client = None
    
    async def summarize_text(self, text: str, style: str = "detailed") -> str:
        """Summarize text using Google Gemini"""
        if not self.client:
            raise Exception("Gemini API not configured. Please set GEMINI_API_KEY environment variable.")
            
        try:
            style_prompts = {
                "brief": "Create a brief 2-3 sentence summary of the key points.",
                "detailed": "Provide a detailed summary with main topics, key insights, and action items.",
                "bullet_points": "Create a bullet-point summary with main topics and subtopics.",
                "executive": "Create an executive summary suitable for business stakeholders."
            }
            
            prompt = style_prompts.get(style, style_prompts["detailed"])
            full_prompt = f"You are an expert at summarizing meeting transcripts and documents. {prompt}\n\nPlease summarize this content:\n\n{text}"
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            
            return response.text or "Unable to generate summary"
            
        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")
    
    async def structured_analysis(self, text: str) -> Dict[str, Any]:
        """Get structured analysis of meeting content"""
        if not self.client:
            raise Exception("Gemini API not configured. Please set GEMINI_API_KEY environment variable.")
            
        try:
            prompt = f"""Extract structured information from this meeting transcript and respond with valid JSON in this exact format:
{{
    "main_topics": ["topic1", "topic2"],
    "key_insights": ["insight1", "insight2"],
    "action_items": ["action1", "action2"],
    "participants": ["person1", "person2"],
    "summary": "brief summary",
    "sentiment": "positive/neutral/negative",
    "duration_estimate": "X minutes"
}}

Transcript:
{text}"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text or "{}")
            return {
                "main_topics": result.get("main_topics", []),
                "key_insights": result.get("key_insights", []),
                "action_items": result.get("action_items", []),
                "participants": result.get("participants", []),
                "summary": result.get("summary", ""),
                "sentiment": result.get("sentiment", "neutral"),
                "duration_estimate": result.get("duration_estimate", "unknown")
            }
            
        except Exception as e:
            raise Exception(f"Structured analysis failed: {str(e)}")
    
    async def answer_question(self, question: str, context: str = "") -> str:
        """Answer questions about meeting content"""
        if not self.client:
            raise Exception("Gemini API not configured. Please set GEMINI_API_KEY environment variable.")
            
        try:
            prompt = "You are a helpful assistant specialized in answering questions about meetings and documents."
            
            if context:
                prompt += f" Use this context to answer questions: {context}"
            
            prompt += f"\n\nQuestion: {question}"
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text or "Unable to answer question"
            
        except Exception as e:
            raise Exception(f"Question answering failed: {str(e)}")
    
    async def generate_action_items(self, text: str) -> list:
        """Extract action items from meeting content"""
        if not self.client:
            raise Exception("Gemini API not configured. Please set GEMINI_API_KEY environment variable.")
            
        try:
            prompt = f"""Extract action items from this meeting transcript. Return as JSON in this format:
{{"action_items": ["item1", "item2", "item3"]}}

Content:
{text}"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text or '{"action_items": []}')
            return result.get("action_items", [])
            
        except Exception as e:
            raise Exception(f"Action item extraction failed: {str(e)}")
    
    async def sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of meeting content"""
        if not self.client:
            raise Exception("Gemini API not configured. Please set GEMINI_API_KEY environment variable.")
            
        try:
            prompt = f"""Analyze the sentiment of this meeting content. Respond with JSON in this format:
{{
    "sentiment": "positive/neutral/negative",
    "score": 3,
    "confidence": 0.8,
    "emotions": ["professional", "collaborative"]
}}

Content:
{text}"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text or '{"sentiment": "neutral", "score": 3, "confidence": 0.5, "emotions": []}')
            return {
                "sentiment": result.get("sentiment", "neutral"),
                "score": max(1, min(5, result.get("score", 3))),
                "confidence": max(0, min(1, result.get("confidence", 0.5))),
                "emotions": result.get("emotions", [])
            }
            
        except Exception as e:
            raise Exception(f"Sentiment analysis failed: {str(e)}")
    
    async def meeting_minutes(self, text: str) -> str:
        """Generate formal meeting minutes"""
        if not self.client:
            raise Exception("Gemini API not configured. Please set GEMINI_API_KEY environment variable.")
            
        try:
            prompt = f"""Generate formal meeting minutes from this transcript. Include attendees, agenda items, decisions, and action items.

Transcript:
{text}"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text or "Unable to generate meeting minutes"
            
        except Exception as e:
            raise Exception(f"Meeting minutes generation failed: {str(e)}")
