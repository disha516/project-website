from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from typing import Optional
import os

# agent_brain.py se functions import ho rahe hain
from agent_brain import get_answer_from_tutor 

app = FastAPI()

# 🌐 CORS Setup (Disha ke frontend ko connect rakhne ke liye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 💾 MongoDB Setup for Feedback
db_client = MongoClient(os.getenv("MONGO_URI"))
db = db_client["jee_solver_db"]
feedback_collection = db["student_feedback"]

# 📝 Pydantic Schema for Feedback
class FeedbackRequest(BaseModel):
    student_query: str
    ai_answer: str
    status: str

# 🎯 DYNAMIC MULTIMODAL ENDPOINT: Handles both JSON and Form-Data gracefully
@app.post("/api/ask")
async def ask_tutor(
    request: Request,
    student_query: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None)
):
    try:
        # 🚀 SMART FALLBACK LAYER: Agar form-data khali hai, toh check karo JSON toh nahi aaya?
        if not student_query and not subject:
            # Check context content-type
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                json_data = await request.json()
                # Extract details safely
                student_query = json_data.get("student_query") or json_data.get("query_text")
                subject = json_data.get("subject") or json_data.get("subject_filter") or "Physics"

        # Content boundary sanity safeguards
        if not student_query:
            raise HTTPException(status_code=422, detail="Missing text data payload. Field 'student_query' is required.")
        
        if not subject:
            subject = "Physics" # Default validation guarantee

        # Files safely read over stream buffers
        image_bytes = await image.read() if image else None
        audio_bytes = await audio.read() if audio else None

        # Call tutor engine matrix
        answer, confidence = get_answer_from_tutor(
            student_query, 
            subject, 
            image_bytes=image_bytes, 
            audio_bytes=audio_bytes
        )

        return {
            "answer": answer,
            "confidence_score": f"{confidence}%"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🌟 FEEDBACK LOOP ENDPOINT
@app.post("/api/feedback")
async def save_feedback(payload: FeedbackRequest):
    try:
        feedback_data = {
            "student_query": payload.student_query,
            "ai_answer": payload.ai_answer,
            "status": payload.status
        }
        feedback_collection.insert_one(feedback_data)
        return {"message": "Feedback successfully saved to MongoDB Cloud!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))