
"""
JEE Solver - Database Seeding Script
Description: Generates high-quality JEE PYQs/problems using Gemini, 
             creates their vector embeddings, and saves them to MongoDB.
"""

import os
import json
from google import genai
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Setup Clients
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
db_client = MongoClient(os.getenv("MONGO_URI"))
db = db_client["jee_solver_db"]  # Apni DB ka naam check kar lena
collection = db["questions"]      # Apni collection ka naam

def generate_jee_questions():
    """Gemini se verified high-quality JEE questions generate karwane ke liye"""
    print("🤖 Gemini se high-quality JEE questions generate ho rahe hain...")
    
    prompt = """
    Generate a list of 15 high-quality, standard IIT-JEE level multiple-choice or numerical problems 
    (7 from Physics like Mechanics, Electrodynamics, RLC circuits; and 8 from Mathematics like Calculus, Vectors, Matrices).
    
    For each question, provide a detailed, verified step-by-step solution to ensure 100% accuracy.
    
    Return the output strictly as a valid JSON array of objects, with NO markdown formatting (do not include ```json or ```). 
    Use this exact JSON structure:
    [
      {
        "subject": "Physics or Mathematics",
        "topic": "Chapter/Topic Name",
        "question_text": "Detailed question statement with standard values",
        "solution_steps": "Detailed step-by-step mathematical solution blueprint"
      }
    ]
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    # JSON clean karke load karna
    clean_text = response.text.strip().lstrip("```json").rstrip("```").strip()
    return json.loads(clean_text)

def seed_database():
    try:
        # 1. Questions generate karo
        raw_questions = generate_jee_questions()
        print(f"✅ {len(raw_questions)} Questions generate ho gaye!")
        
        # 2. Har question ka embedding banakar DB mein daalo
        print("🚀 Ab har question ka vector embedding banakar MongoDB mein insert kar rahe hain...")
        
        inserted_count = 0
        for item in raw_questions:
            # Combined text banate hain taaki text search aur vector dono strong rahein
            text_to_embed = f"Subject: {item['subject']} | Topic: {item['topic']} | Question: {item['question_text']}"
            
            # Gemini Embedding Model call
            embed_response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text_to_embed
            )
            
            # Vector extract karo
            vector = embed_response.embeddings[0].values
            
            # Document mein embedding jodo
            item["question_embedding"] = vector
            
            # MongoDB mein save karo
            collection.insert_one(item)
            inserted_count += 1
            print(f"[{inserted_count}/{len(raw_questions)}] Inserted: {item['topic']}")
            
        print(f"\n🎉 MUBARAK HO! Saare {inserted_count} questions embeddings ke sath MongoDB mein successfully load ho gaye hain!")

    except Exception as e:
        print("❌ Error occurred during seeding:", e)

if __name__ == "__main__":
    seed_database()