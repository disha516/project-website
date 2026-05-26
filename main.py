
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent_brain import get_answer_from_tutor

app = FastAPI(title="JEE Solver API Server")

# CORS Settings: Yeh tumhari teammate ke frontend ko tumhare backend se bina security block ke connect karega
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hackathon ke liye development phase mein sab allow kar dete hain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend se jo data aayega uska format (Data Contract)
class QueryRequest(BaseModel):
    student_query: str
    subject: str

@app.get("/")
def home():
    return {"status": "success", "message": "JEE Backend Server is Running Live!"}

@app.post("/api/ask")
def ask_tutor(request: QueryRequest):
    """
    This endpoint takes the student's query and subject from the frontend,
    passes it to our MongoDB+Gemini engine, and returns the response.
    """
    try:
        print(f" Received query for {request.subject}: {request.student_query}")
        
        # Calling our core engine function
        ai_response = get_answer_from_tutor(request.student_query, request.subject)
        
        return {
            "status": "success",
            "backend_status": "Connected to MongoDB Atlas & Gemini",
            "response": ai_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))