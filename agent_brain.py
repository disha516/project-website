"""
JEE Solver Agent — retrieval-grounded, multimodal tutoring engine.
"""

import os
import io
import PIL.Image
from google import genai
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
db_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=5000)
db = db_client["jee_solver_db"]
collection = db["questions"]

# Per-process cache for repeated text questions.
query_cache = {}


def get_embedding(text: str):
    """Create a 768-dimensional query vector matching the Atlas index contract."""
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return response.embeddings[0].values[:768]


def search_similar_questions(student_query: str, subject: str):
    """Retrieve candidates, then select the best candidate belonging to the chosen subject."""
    print(f"[VECTOR SEARCH] Starting retrieval for subject={subject!r}")
    query_vector = get_embedding(student_query)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "question_embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": 20,
            }
        },
        {
            "$project": {
                "subject": 1,
                "topic": 1,
                "question_text": 1,
                "solution_steps": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    candidates = list(collection.aggregate(pipeline))
    print(f"[VECTOR SEARCH] Atlas returned {len(candidates)} candidate(s) before subject filtering")
    normalized_subject = "Mathematics" if subject.lower() in {"maths", "mathematics"} else subject.title()
    matches = [doc for doc in candidates if doc.get("subject", "").lower() == normalized_subject.lower()]
    print(f"[VECTOR SEARCH] Subject={normalized_subject!r}; matching question(s)={len(matches)}")
    return matches


def get_answer_from_tutor(
    student_query: str = "",
    subject: str = "Physics",
    difficulty: str = "Easy",
    search_priority: str = "Vector Database (Fast)",
    image_bytes=None,
    audio_bytes=None,
):
    """Generate a step-by-step answer, optionally grounded by a subject-matched Atlas reference."""
    clean_query = (student_query or "").strip()
    cache_key = f"{subject.lower()}|{difficulty.lower()}|{search_priority.lower()}|{clean_query.lower()}"

    if clean_query and not image_bytes and not audio_bytes and cache_key in query_cache:
        cached = query_cache[cache_key]
        return cached["answer"], cached["match_score"]

    context_data = ""
    match_score = 0.0

    # "Full AI Engine Fallback" intentionally bypasses vector retrieval.
    if search_priority == "Full AI Engine Fallback":
        print("[SOLVER MODE] Full AI Engine Fallback selected; vector retrieval skipped")
    if (
        search_priority == "Vector Database (Fast)"
        and clean_query
        and len(clean_query) > 3
    ):
        try:
            similar_docs = search_similar_questions(clean_query, subject)
            if similar_docs:
                best_match = similar_docs[0]
                match_score = round(float(best_match.get("score", 0.0)) * 100, 1)
                print("[SOLVER MODE] Retrieved database context will be supplied to Gemini")
                context_data = (
                    "Relevant reference from the selected subject's question database:\n"
                    f"Question: {best_match.get('question_text', '')}\n"
                    f"Solution blueprint: {best_match.get('solution_steps', '')}"
                )
        except Exception as exc:
            # Retrieval is optional; preserve the Gemini fallback but log the failure for operators.
            print(f"[VECTOR SEARCH UNAVAILABLE] {type(exc).__name__}: {exc}")
    elif search_priority == "Vector Database (Fast)" and not clean_query:
        print("[VECTOR SEARCH] Skipped because the request contains no text query")
    if search_priority == "Vector Database (Fast)" and clean_query and not context_data:
        print("[SOLVER MODE] No matching database context; Gemini will answer without retrieved PYQ context")

    difficulty_guidance = {
        "Easy": "Explain foundational concepts slowly and show each basic step.",
        "Medium": "Use standard JEE-level reasoning and show the important intermediate steps.",
        "Hard": "Use challenging JEE-level reasoning, justify non-obvious steps, and check the result.",
        "JEE Advanced": "Use rigorous JEE Advanced-level reasoning, consider useful alternate approaches, and justify assumptions.",
    }.get(difficulty, "Use standard JEE-level reasoning and show the important intermediate steps.")

    prompt = f"""
You are an expert IIT-JEE tutor specializing in {subject}.
Requested problem level: {difficulty}.
Difficulty guidance: {difficulty_guidance}

Student question: {clean_query if clean_query else "Please solve the attached image or voice question."}
{context_data}

Instructions:
1. If an image is attached, read the problem carefully and solve it step by step.
2. If audio is attached, understand the spoken doubt and answer it.
3. Use retrieved database material only as supporting reference; independently check the reasoning.
4. Write mathematical expressions using standard LaTeX.
5. Match the student's language: use Hindi/Hinglish for Hindi/Hinglish questions and English for English questions.
6. State assumptions if the question is ambiguous. Do not invent missing values.
7. Present a clear, structured solution and a final answer.
"""

    contents = [prompt]
    if image_bytes:
        image = PIL.Image.open(io.BytesIO(image_bytes))
        contents.append(image)

    if audio_bytes:
        from google.genai import types
        contents.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"))

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
    )
    final_answer = response.text or "I could not generate an answer. Please try again."

    if clean_query and not image_bytes and not audio_bytes:
        query_cache[cache_key] = {"answer": final_answer, "match_score": match_score}

    return final_answer, match_score
