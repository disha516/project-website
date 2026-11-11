from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from typing import Optional
import os

from agent_brain import get_answer_from_tutor

app = FastAPI(title="JEE Solver Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB clients are lazy: the app can start even if Atlas is temporarily unavailable.
db_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=5000)
db = db_client["jee_solver_db"]
feedback_collection = db["student_feedback"]


class FeedbackRequest(BaseModel):
    student_query: str
    ai_answer: str
    status: str


@app.get("/health")
async def health():
    """Lightweight process health check; does not claim MongoDB is reachable."""
    return {"status": "ok", "service": "jee-solver-agent"}


@app.post("/api/ask")
async def ask_tutor(
    request: Request,
    student_query: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    difficulty: Optional[str] = Form("Easy"),
    search_priority: Optional[str] = Form("Vector Database (Fast)"),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
):
    try:
        if "application/json" in request.headers.get("content-type", ""):
            json_data = await request.json()
            student_query = student_query or json_data.get("student_query") or json_data.get("query_text")
            subject = subject or json_data.get("subject") or json_data.get("subject_filter")
            difficulty = json_data.get("difficulty") or difficulty
            search_priority = json_data.get("search_priority") or search_priority

        subject = subject or "Physics"
        difficulty = difficulty or "Easy"
        search_priority = search_priority or "Vector Database (Fast)"

        allowed_subjects = {"Physics", "Chemistry", "Mathematics"}
        allowed_difficulties = {"Easy", "Medium", "Hard", "JEE Advanced"}
        allowed_priorities = {"Vector Database (Fast)", "Full AI Engine Fallback"}

        if subject not in allowed_subjects:
            raise HTTPException(status_code=422, detail="Invalid subject selection.")
        if difficulty not in allowed_difficulties:
            raise HTTPException(status_code=422, detail="Invalid difficulty selection.")
        if search_priority not in allowed_priorities:
            raise HTTPException(status_code=422, detail="Invalid search priority.")

        image_bytes = await image.read() if image else None
        audio_bytes = await audio.read() if audio else None
        if not (student_query or "").strip() and not image_bytes and not audio_bytes:
            raise HTTPException(status_code=422, detail="Enter a question or attach an image/voice note.")

        answer, match_score = get_answer_from_tutor(
            student_query or "",
            subject,
            difficulty=difficulty,
            search_priority=search_priority,
            image_bytes=image_bytes,
            audio_bytes=audio_bytes,
        )

        # Keep the retrieval signal for diagnostics only; the student UI does not show it as confidence.
        return {"answer": answer, "database_match_score": match_score}

    except HTTPException:
        raise
    except Exception:
        # Avoid returning internal exception details, credentials, or infrastructure data to clients.
        raise HTTPException(status_code=500, detail="The solver could not complete this request. Please try again.")


@app.post("/api/feedback")
async def save_feedback(payload: FeedbackRequest):
    try:
        if payload.status not in {"Correct", "Incorrect"}:
            raise HTTPException(status_code=422, detail="Feedback status must be Correct or Incorrect.")
        feedback_collection.insert_one({
            "student_query": payload.student_query,
            "ai_answer": payload.ai_answer,
            "status": payload.status,
        })
        return {"message": "Feedback successfully saved."}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Feedback could not be saved right now.")
