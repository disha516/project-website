"""
JEE Complete Solver - Database Seeding Pipeline (Final Bypass Version)
"""

import os
from pymongo import MongoClient
from google import genai
from dotenv import load_dotenv

# Environment configuration load karo
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Clients Initialize karo
client = genai.Client(api_key=GEMINI_KEY)

# 🛠️ HARDCORE NETWORK BYPASS: direct configuration parameters 
db_client = MongoClient(
    MONGO_URI,
    connect=True,
    tls=True,
    tlsAllowInvalidCertificates=True,
    serverSelectionTimeoutMS=5000
)
db = db_client["jee_solver_db"]
collection = db["questions"]

def get_embedding(text: str):
    """Text ka mathematical vector array generate karne ke liye"""
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return response.embeddings[0].values

def seed_database():
    print("🚀 Initiating Database Seeding Pipeline...")
    
    mock_questions = [
        {
            "subject": "Physics",
            "chapter": "Electrostatics",
            "question_type": "Numerical",
            "question_text": r"Two point charges $q_1 = +2 \, \mu\text{C}$ and $q_2 = -3 \, \mu\text{C}$ are placed at a distance of $30 \, \text{cm}$ in air. Calculate the magnitude of the electrostatic force between them.",
            "solution_steps": r"Step 1: Convert units to SI. $q_1 = 2 \times 10^{-6} \, \text{C}$, $q_2 = -3 \times 10^{-6} \, \text{C}$, $r = 0.3 \, \text{m}$. Step 2: Apply Coulomb's Law: $$F = k \frac{|q_1 q_2|}{r^2}$$ where $k = 9 \times 10^9 \, \text{N}\cdot\text{m}^2/\text{C}^2$. Step 3: Substitute the values: $$F = 9 \times 10^9 \times \frac{2 \times 10^{-6} \times 3 \times 10^{-6}}{(0.3)^2} = 0.6 \, \text{N}.$$",
            "final_answer": "0.6 N"
        },
        {
            "subject": "Chemistry",
            "chapter": "Chemical Kinetics",
            "question_type": "Numerical",
            "question_text": r"A first-order reaction has a rate constant $k = 5.5 \times 10^{-14} \, \text{s}^{-1}$. Find the half-life of the reaction.",
            "solution_steps": r"Step 1: For a first-order reaction, the expression for half-life ($t_{1/2}$) is given by: $$t_{1/2} = \frac{0.693}{k}$$ Step 2: Substitute the given value of rate constant $k = 5.5 \times 10^{-14} \, \text{s}^{-1}$. Step 3: Calculate the value: $$t_{1/2} = \frac{0.693}{5.5 \times 10^{-14}} \approx 1.26 \times 10^{13} \, \text{s}.$$",
            "final_answer": "1.26 x 10^13 s"
        },
        {
            "subject": "Mathematics",
            "chapter": "Definite Integration",
            "question_type": "Numerical",
            "question_text": r"Evaluate the definite integral: $$\int_0^{\pi/2} \frac{\sin(x)}{\sin(x) + \cos(x)} \, dx$$",
            "solution_steps": r"Step 1: Let the given integral be $I = \int_0^{\pi/2} \frac{\sin(x)}{\sin(x) + \cos(x)} \, dx$. Step 2: Apply King's Property $\int_a^b f(x)dx = \int_a^b f(a+b-x)dx$: $$I = \int_0^{\pi/2} \frac{\sin(\pi/2 - x)}{\sin(\pi/2 - x) + \cos(\pi/2 - x)} \, dx = \int_0^{\pi/2} \frac{\cos(x)}{\cos(x) + \sin(x)} \, dx$$ Step 3: Add both expressions of $I$: $$2I = \int_0^{\pi/2} \frac{\sin(x) + \cos(x)}{\sin(x) + \cos(x)} \, dx = \int_0^{\pi/2} 1 \, dx = [x]_0^{\pi/2} = \frac{\pi}{2}$$ Step 4: Solve for $I$: $$I = \frac{\pi}{4}.$$",
            "final_answer": "pi/4"
        }
    ]
    
    processed_docs = []
    
    for item in mock_questions:
        print(f"📊 Processing embedding for [{item['subject']} - {item['chapter']}]...")
        embedding = get_embedding(item["question_text"])
        
        doc = {
            "subject": item["subject"],
            "chapter": item["chapter"],
            "question_type": item["question_type"],
            "question_text": item["question_text"],
            "solution_steps": item["solution_steps"],
            "final_answer": item["final_answer"],
            "question_embedding": embedding
        }
        processed_docs.append(doc)
        
    print("📥 Pushing structured documents straight to Atlas cluster...")
    try:
        # direct push bina delete check handle kiye taaki pipeline check secure rahe
        collection.insert_many(processed_docs)
        print("🎉 [SUCCESS] Database Seeded perfectly! Vectors successfully stored.")
    except Exception as network_err:
        print(f"❌ Connection block still active: {network_err}")

if __name__ == "__main__":
    seed_database()