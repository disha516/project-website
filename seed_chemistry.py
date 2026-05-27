"""
JEE Solver - Chemistry Data Seeding Script
Description: Generates 10 high-quality JEE Chemistry problems using Gemini, 
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
db = db_client["jee_solver_db"]
collection = db["questions"]

def generate_chemistry_questions():
    print("🧪 Gemini se high-quality JEE CHEMISTRY questions generate ho rahe hain...")
    
    prompt = """
    Generate a list of 10 high-quality, standard IIT-JEE level Chemistry problems 
    covering Organic, Inorganic, and Physical Chemistry (e.g., Chemical Kinetics, 
    Thermodynamics, Coordination Compounds, Reaction Mechanisms).
    
    For each question, provide a detailed, verified step-by-step solution to ensure 100% accuracy.
    
    Return the output strictly as a valid JSON array of objects, with NO markdown formatting. 
    Use this exact JSON structure:
    [
      {
        "subject": "Chemistry",
        "topic": "Chapter/Topic Name",
        "question_text": "Detailed question statement with standard values",
        "solution_steps": "Detailed step-by-step molecular or mathematical solution blueprint"
      }
    ]
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    clean_text = response.text.strip().lstrip("```json").rstrip("```").strip()
    return json.loads(clean_text)

def seed_chemistry():
    try:
        raw_questions = generate_chemistry_questions()
        print(f"✅ {len(raw_questions)} Chemistry Questions generate ho gaye!")
        
        print("🚀 Vector embeddings banakar MongoDB mein daal rahe hain...")
        inserted_count = 0
        for item in raw_questions:
            text_to_embed = f"Subject: Chemistry | Topic: {item['topic']} | Question: {item['question_text']}"
            
            embed_response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text_to_embed
            )
            
            item["question_embedding"] = embed_response.embeddings[0].values
            collection.insert_one(item)
            inserted_count += 1
            print(f"[{inserted_count}/{len(raw_questions)}] Inserted Chemistry: {item['topic']}")
            
        print("\n🎉 BADIYA! Chemistry ka data bhi successfully load ho gaya!")

    except Exception as e:
        print("❌ Error during Chemistry seeding:", e)

if __name__ == "__main__":
    seed_chemistry()