"""
JEE Complete Solver - AI Grounding & Query Engine (Advanced Version)
Features: MongoDB Vector Search, Confidence Scoring, and Fast Caching.
"""

import os
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
# Key: "subject_student_query" -> Value: {"answer": "...", "confidence": ...}
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
                "limit": 1  # Humein bas sabse best match chahiye score ke liye
            }
        },
        {
            # PROJECT STEP: Isse MongoDB humein similarity score nikal kar deta hai
            "$project": {
                "subject": 1,
                "topic": 1,
                "question_text": 1,
                "solution_steps": 1,
                "score": {"$meta": "vectorSearchScore"}  # Confidence Score nikalne ka fanda
            }
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    return results

def get_answer_from_tutor(student_query: str, subject: str):
    """Main function loaded with Caching, Vector Search, and Scoring"""
    
    # 🌟 FEATURE 1: CACHE CHECK
    cache_key = f"{subject.lower()}_{student_query.strip().lower()}"
    if cache_key in query_cache:
        print("⚡ [CACHE HIT] Yeh sawal pehle pucha ja chuka hai. Instant response bhej rahe hain!")
        return query_cache[cache_key]["answer"], query_cache[cache_key]["confidence"]

    print("🔍 [CACHE MISS] Naya sawal hai. Database aur Gemini processing shuru...")
    
    context_data = ""
    confidence_score = 0.0  # Default agar database mein kuch na mile
    
    # 🌟 FEATURE 2: VECTOR SEARCH WITH SCORE
    try:
        similar_docs = search_similar_questions(student_query)
        if similar_docs:
            best_match = similar_docs[0]
            # MongoDB score ko percentage (0-100%) mein badal rahe hain
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

    # 3. GEMINI PROMPT & GENERATION
    prompt = f"""
    You are an expert IIT-JEE tutor specializing in {subject}.
    
    Student Query: {student_query}
    {context_data}
    
    Instructions:
    1. Solve the student query step-by-step.
    2. If a database reference is provided above, use its core logic/formula to ground your answer and avoid hallucinations.
    3. Output the final answer beautifully with clear headers.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    final_answer = response.text
    
    # 🌟 SAVE TO CACHE (Taaki agli baar instant load ho)
    query_cache[cache_key] = {
        "answer": final_answer,
        "confidence": confidence_score
    }
    
    return final_answer, confidence_score