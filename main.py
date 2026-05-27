from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
from agent_brain import get_answer_from_tutor

app = FastAPI()

# CORS Setup (Disha ke frontend ko connect rakhne ke liye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Setup for Feedback
db_client = MongoClient(os.getenv("MONGO_URI"))
db = db_client["jee_solver_db"]
feedback_collection = db["student_feedback"]

# Pydantic Schemas
class QueryRequest(BaseModel):
    student_query: str
    subject: str

class FeedbackRequest(BaseModel):
    student_query: str
    ai_answer: str
    status: str  # Isme frontend "thumbs_up" ya "thumbs_down" bhegega

@app.post("/api/ask")
async def ask_tutor(payload: QueryRequest):
    try:
        # get_answer_from_tutor ab do cheezein return karta hai: answer aur confidence
        answer, confidence = get_answer_from_tutor(payload.student_query, payload.subject)
        
        # Frontend ko dono cheezein ek JSON mein bhej rahe hain
        return {
            "answer": answer,
            "confidence_score": f"{confidence}%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🌟 FEATURE 3: FEEDBACK LOOP ENDPOINT
@app.post("/api/feedback")
async def receive_feedback(payload: FeedbackRequest):
    try:
        feedback_data = {
            "student_query": payload.student_query,
            "ai_answer": payload.ai_answer,
            "status": payload.status,
            "timestamp": os.getenv("CURRENT_TIME", "2026") # Simple tracker
        }
        # Database mein student ka feedback insert ho raha hai
        feedback_collection.insert_one(feedback_data)
        return {"message": "Feedback successfully saved to MongoDB!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))