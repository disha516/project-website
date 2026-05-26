"""
JEE Complete Solver - AI Grounding & Query Engine
Description: This script fetches verified question blueprints from MongoDB Atlas 
             and feeds them as context to Gemini 2.5 Flash to ensure 100% accurate, 
             hallucination-free tutoring.
"""

import os
from pymongo import MongoClient
from google import genai
from dotenv import load_dotenv

# Load credentials securely
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

def get_answer_from_tutor(student_query, subject_filter):
    """
    Fetches the verified answer from MongoDB based on subject, 
    and uses Gemini to explain it cleanly to the student.
    """
    try:
        # 1. Connect to MongoDB and find the question
        client = MongoClient(MONGO_URI)
        db = client["JEE_Database"]
        collection = db["questions"]
        
        # Simple text search inside our collection based on subject
        # (In next steps, we will upgrade this to advanced Vector Search!)
        verified_data = collection.find_one({"subject": subject_filter})
        
        if not verified_data:
            return f"Sorry, mujhe database mein {subject_filter} ka koi verified question nahi mila."

        # 2. Extract fields from our Team Data Contract
        question_text = verified_data.get("question_text")
        verified_sol = verified_data.get("verified_solution")
        final_ans = verified_data.get("final_answer")

        # 3. Initialize the latest Gemini Client
        ai_client = genai.Client()

        # 4. Craft a Strict System Prompt (Grounding)
        # This forces Gemini to act like an expert IIT Coach and not make up answers.
        system_instruction = (
            "You are an expert IIT-JEE Tutor. Your job is to explain the question below to a student. "
            "CRITICAL: You MUST base your explanation completely on the Provided Verified Solution. "
            "Do not hallucinate. Use clear step-by-step logic, explain the formulas, and state the final answer clearly."
        )

        prompt = f"""
        System Instruction: {system_instruction}
        
        --- Verified Data from Database ---
        Question: {question_text}
        Verified Reference Steps: {verified_sol}
        Target Final Answer: {final_ans}
        
        --- Student Query ---
        Student wants to know: "{student_query}"
        
        Please provide a beautifully formatted explanation:
        """

        # 5. Generate content using the new SDK standard
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        return response.text.strip()

    except Exception as e:
        return f"Engine Error: {e}"


# --- LOCAL TEST PIPELINE ---
if __name__ == "__main__":
    print(" testing the Full Grounding Engine Pipeline...")
    
    # Simulating a user asking a question on the frontend
    sample_query = "Please explain the Electrostatics numerical step-by-step and tell me the force."
    sample_subject = "Physics"
    
    ai_response = get_answer_from_tutor(sample_query, sample_subject)
    
    print("\n✨ FINAL RESPONSE FOR FRONTEND:")
    print(ai_response)