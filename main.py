from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os

# `agent_brain.py` se naya functions import kar rahe hain
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

# 📝 Pydantic Schema (Sirf Feedback ke liye chahiye ab, kyunki ask Form-Data use karega)
class FeedbackRequest(BaseModel):
    student_query: str
    ai_answer: str
    status: str  # Isme frontend "thumbs_up" ya "thumbs_down" bhejega

# 🎯 MULTIMODAL ENDPOINT: /api/ask (Handles Text, Images, and Audio)
@app.post("/api/ask")
async def ask_tutor(
    student_query: str = Form(None), # Default value None set kar di taaki crash na ho
    
    subject: str = Form(...),
    image: UploadFile = File(None),  # Optional image file
    audio: UploadFile = File(None)   # Optional audio file
):
    try:
        # Files ko bytes mein read karo agar woh exist karti hain
        image_bytes = await image.read() if image else None
        audio_bytes = await audio.read() if audio else None

        # `get_answer_from_tutor` ko saare multimodal inputs pass kar do
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

# 🌟 FEEDBACK LOOP ENDPOINT: /api/feedback
@app.post("/api/feedback")
async def save_feedback(payload: FeedbackRequest):
    try:
        feedback_data = {
            "student_query": payload.student_query,
            "ai_answer": payload.ai_answer,
            "status": payload.status
        }
        # Database mein student ka feedback insert ho raha hai
        feedback_collection.insert_one(feedback_data)
        return {"message": "Feedback successfully saved to MongoDB Cloud!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))