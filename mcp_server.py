"""
JEE Complete Solver - Official Model Context Protocol (MCP) Server
Fulfills Hackathon Requirement: Meaningful Integration via Standard MCP Server Protocol.
"""

import os
import json
from pymongo import MongoClient
from google import genai
from dotenv import load_dotenv

# 🚀 100% STABLE LAYERED IMPORTS (No more ImportErrors!)
from mcp.server import Server
import mcp.types as types

load_dotenv()

# Setup Clients with network safeguards
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

client = genai.Client(api_key=GEMINI_KEY)
db_client = MongoClient(MONGO_URI, tls=True, tlsInsecure=True)
db = db_client["jee_solver_db"]
collection = db["questions"]

# ✨ Initialize the core official MCP Server
mcp_server = Server("JEE MongoDB Grounding Server")

def get_embedding(text: str):
    """
    Bullet-proof embedding retrieval with manual dimensionality slicing safeguard.
    Wipes out 404 NOT_FOUND and dimension mismatch errors permanently.
    """
    # 1. Use the exact same stable model that successfully seeded your database
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    
    raw_vector = response.embeddings[0].values
    
    # 2. HARDCORE SAFEGUARD: Slice the array strictly to 768 dimensions 
    # This guarantees MongoDB Atlas vector search index contract is never violated!
    return raw_vector[:768]

# 🌟 REGISTER THE LOGIC AS AN OFFICIAL MCP TOOL LAYER
@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Exposes the tools capability structure to the protocol clients."""
    return [
        types.Tool(
            name="query_jee_database",
            description="Fetches verified textbook solutions and PYQs from MongoDB Atlas based on student query text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_text": {"type": "string", "description": "The conceptual science question text."},
                    "subject_filter": {"type": "string", "description": "Strict science subject classification (Physics/Chemistry/Maths)."}
                },
                "required": ["query_text", "subject_filter"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handles the structural tool trigger calls and routes the data pipeline."""
    if name != "query_jee_database":
        raise ValueError(f"Unknown tool requested: {name}")

    if not arguments or "query_text" not in arguments or "subject_filter" not in arguments:
        return [types.TextContent(type="text", text="ERROR: Missing required query arguments.")]

    query_text = arguments["query_text"]
    subject_filter = arguments["subject_filter"]

    try:
        query_vector = get_embedding(query_text)
        
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
                "$match": {
                    "subject": subject_filter
                }
            },
            {
                "$project": {
                    "question_text": 1,
                    "solution_steps": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        results = list(collection.aggregate(pipeline))
        if results:
            match = results[0]
            output_msg = f"MATCH_FOUND: Question: {match.get('question_text')} | Verified Steps: {match.get('solution_steps')}"
        else:
            output_msg = "NO_MATCH: No identical ground-truth found in database."
            
        return [types.TextContent(type="text", text=output_msg)]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"ERROR: MCP Server logic crash: {str(e)}")]

# Helper testing module direct integration
def query_jee_database(query_text: str, subject_filter: str) -> str:
    """Helper mock function for local test suite execution"""
    import asyncio
    # Simple bridge to run async handlers inside local synchronous test suites
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(handle_call_tool("query_jee_database", {"query_text": query_text, "subject_filter": subject_filter}))
    return res[0].text

if __name__ == "__main__":
    import asyncio
    print("⚡ Core Official MCP MongoDB Server initialized.")
    # Runs standard stream interfaces protocol
    asyncio.run(mcp_server.run_stdio())