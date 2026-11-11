"""
JEE Solver - Database Seeding Script.
"""

import os
import json
from google import genai
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
db_client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
collection = db_client["jee_solver_db"]["questions"]


def generate_jee_questions():
    prompt = """
    Generate 15 JEE-level multiple-choice or numerical problems:
    7 Physics and 8 Mathematics, covering mechanics, electrodynamics,
    calculus, vectors, and matrices. Include detailed step-by-step solutions.
    Return only a valid JSON array with subject, topic, question_text,
    and solution_steps fields.
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    clean_text = response.text.strip()
    if clean_text.startswith("```"):
        clean_text = clean_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(clean_text)


def seed_database():
    raw_questions = generate_jee_questions()
    for item in raw_questions:
        text_to_embed = (
            f"Subject: {item['subject']} | Topic: {item['topic']} | "
            f"Question: {item['question_text']}"
        )
        embedding = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text_to_embed,
        ).embeddings[0].values[:768]
        item["question_embedding"] = embedding
        collection.insert_one(item)
        print(f"Inserted: {item['subject']} - {item['topic']}")


if __name__ == "__main__":
    seed_database()
