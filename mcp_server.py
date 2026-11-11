"""
JEE Solver Agent — MCP interface to the MongoDB Atlas question collection.
"""

import os
from pymongo import MongoClient
from google import genai
from dotenv import load_dotenv
from mcp.server import Server
import mcp.types as types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
db_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=5000)
collection = db_client["jee_solver_db"]["questions"]
mcp_server = Server("JEE MongoDB Grounding Server")


def get_embedding(text: str):
    response = client.models.embed_content(model="gemini-embedding-001", contents=text)
    return response.embeddings[0].values[:768]


@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="query_jee_database",
            description="Retrieves a relevant JEE question and solution from MongoDB Atlas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_text": {"type": "string"},
                    "subject_filter": {"type": "string", "enum": ["Physics", "Chemistry", "Mathematics", "Maths"]},
                },
                "required": ["query_text", "subject_filter"],
            },
        )
    ]


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name != "query_jee_database":
        raise ValueError(f"Unknown tool requested: {name}")
    if not arguments or not arguments.get("query_text") or not arguments.get("subject_filter"):
        return [types.TextContent(type="text", text="ERROR: query_text and subject_filter are required.")]

    subject = arguments["subject_filter"]
    if subject.lower() == "maths":
        subject = "Mathematics"

    try:
        vector = get_embedding(arguments["query_text"])
        candidates = list(collection.aggregate([
            {"$vectorSearch": {
                "index": "vector_index",
                "path": "question_embedding",
                "queryVector": vector,
                "numCandidates": 100,
                "limit": 20,
            }},
            {"$project": {
                "subject": 1,
                "question_text": 1,
                "solution_steps": 1,
                "score": {"$meta": "vectorSearchScore"},
            }},
        ]))
        matches = [doc for doc in candidates if doc.get("subject", "").lower() == subject.lower()]
        if not matches:
            return [types.TextContent(type="text", text="NO_MATCH: No reference found for the selected subject.")]
        match = matches[0]
        output = (
            f"MATCH_FOUND: Question: {match.get('question_text')} | "
            f"Solution: {match.get('solution_steps')} | Score: {match.get('score', 0)}"
        )
        return [types.TextContent(type="text", text=output)]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"ERROR: Database retrieval unavailable: {type(exc).__name__}")]


if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp_server.run_stdio())
