"""
JEE Complete Solver - AI Grounding & Query Engine (Advanced Multimodal Version)
Features: MongoDB Vector Search, Confidence Scoring, Fast Caching, Image OCR, and Voice Analysis.
"""

import os
import io
import PIL.Image
from google import genai
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Setup Clients
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
db_client = MongoClient(os.getenv("MONGO_URI"))
db = db_client["jee_solver_db"]
collection = db["questions"]

# 1. SIMPLE IN-MEMORY CACHE
query_cache = {}

def get_embedding(text: str):
    """Student ki query ko mathematical vector mein badalne ke liye"""
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return response.embeddings[0].values

def search_similar_questions(student_query: str):
    """MongoDB vector search chalakar sabse close question aur uska confidence score dhoondne ke liye"""
    query_vector = get_embedding(student_query)
    
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "question_embedding",
                "queryVector": query_vector,
                "numCandidates": 10,
                "limit": 1
            }
        },
        {
            "$project": {
                "subject": 1,
                "topic": 1,
                "question_text": 1,
                "solution_steps": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    return results

def get_answer_from_tutor(student_query: str = None, subject: str = "Physics", image_bytes=None, audio_bytes=None):
    """Main function loaded with Caching, Vector Search, Scoring, and Multimodal Support"""
    
    # Safe fallback if text query is missing or None
    safe_query = student_query if student_query is not None else ""
    clean_query = safe_query.strip()
    
    if not clean_query:
        clean_query = "multimodal_media_query"

    # 🌟 FEATURE 1: CACHE CHECK
    cache_key = f"{subject.lower()}_{clean_query.lower()}"
    if not image_bytes and not audio_bytes and cache_key in query_cache:
        print("⚡ [CACHE HIT] Yeh sawal pehle pucha ja chuka hai. Instant response bhej rahe hain!")
        return query_cache[cache_key]["answer"], query_cache[cache_key]["confidence"]

    print("🔍 [CACHE MISS] Processing request through Database and Multimodal Gemini...")
    
    context_data = ""
    confidence_score = 0.0
    
    # 🌟 FEATURE 2: VECTOR SEARCH (Sirf tab chalega jab student ne dhang ka text pucha ho)
    if student_query and len(clean_query) > 3 and clean_query != "multimodal_media_query":
        try:
            similar_docs = search_similar_questions(student_query)
            if similar_docs:
                best_match = similar_docs[0]
                confidence_score = round(best_match.get("score", 0.0) * 100, 1)
                
                context_data = f"""
                Here is a verified reference question from our database with {confidence_score}% logic match:
                Question: {best_match.get('question_text', '')}
                Solution Blueprint: {best_match.get('solution_steps', '')}
                """
                print(f"🎯 Database match mila! Confidence Score: {confidence_score}%")
            else:
                print("Database mein koi relevant match nahi mila.")
        except Exception as e:
            print("Vector search score extraction error:", e)

   # 3. GEMINI PROMPT SETUP (Upgraded with Language & Mode Matching)
    prompt = fr"""
    You are an expert IIT-JEE tutor specializing in {subject}.
    
    Student Text Query: {student_query if student_query else "See attached media input."}
    {context_data}
    
    Instructions:
    1. If an image is attached, perform OCR and understand the mathematical problem shown. Solve it step-by-step.
    2. If an audio file is attached, listen carefully to the student's voice query and address it professionally.
    3. If a database reference is provided above, use its core logic/formula to ground your answer and avoid hallucinations.
    4. FORMATTING RULE: Write ALL mathematical expressions, equations, formulas, and variables strictly using standard LaTeX. 
       - Use inline LaTeX with a single dollar sign like $e = mc^2$ for equations within text.
       - Use block display LaTeX with double dollar signs like $$I = \int_0^\pi \sin(x) \, dx$$ for standalone equations.
    5. LANGUAGE & MODE MATCHING RULE (CRITICAL): Maintain the exact same language, tone, and mode used by the student.
       - If the student asks or speaks in Hinglish/Hindi, explain the conceptual steps in Hinglish/Hindi (while keeping technical terms and LaTeX formulas in standard form).
       - If the student asks in English, respond fully in English.
       - Match the depth and medium of the student's query naturally.
    6. Output the final answer beautifully with clear markdown headers.
    """

    # 🌟 NEW MULTIMODAL CONTENTS LIST
    contents = [prompt]

    # Handling Image Data if provided by Disha's Frontend
    if image_bytes:
        print("📸 Input Type Detected: Image. Loading matrix data for Gemini Vision...")
        img = PIL.Image.open(io.BytesIO(image_bytes))
        contents.append(img)

    # Handling Audio Data if provided by Disha's Frontend
   
    if audio_bytes:
        print("🎤 Input Type Detected: Audio/Voice. Binding audio stream for Gemini Listen...")
        
        # Naye SDK ke liye formal parts format import karna hoga function ke andar hi
        from google.genai import types
        
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type="audio/wav"
        )
        contents.append(audio_part)
        

    # Calling the advanced gemini-2.5-flash model which natively supports multimodality
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents
    )
    
    final_answer = response.text
    
    # SAVE TO CACHE (Only cache text queries to prevent memory overflow from large file buffers)
    if not image_bytes and not audio_bytes:
        query_cache[cache_key] = {
            "answer": final_answer,
            "confidence": confidence_score
        }
    
    return final_answer, confidence_score