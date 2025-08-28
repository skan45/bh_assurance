import os
import re
import json
import hashlib
from datetime import datetime, timezone
from qdrant_client import QdrantClient
from fastembed import TextEmbedding
from db import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis

load_dotenv()

# ----------------- Environment & Configuration -----------------
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "docs_embeddings")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USER = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "")

# Redis config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_EXPIRATION = 3600  # 1 hour

# ----------------- Redis Connection -----------------
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def make_cache_key(query: str) -> str:
    """Generate a unique cache key for a query."""
    return hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()

# ----------------- Unified History -----------------
UNIFIED_HISTORY_FILE = "unified_conversation_history.json"
unified_history: List[Dict[str, str]] = []

def load_unified_history():
    global unified_history
    try:
        if os.path.exists(UNIFIED_HISTORY_FILE):
            with open(UNIFIED_HISTORY_FILE, "r", encoding="utf-8") as f:
                unified_history = json.load(f)
    except Exception as e:
        print(f"Error loading unified history: {e}")
        unified_history = []

def save_unified_history():
    try:
        with open(UNIFIED_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(unified_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving unified history: {e}")

load_unified_history()

# ----------------- Conversation Memory for Qdrant -----------------
conversation_history = []
CONVERSATION_FILE = "conversation_history.json"

def save_conversation_to_file():
    try:
        with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving conversation: {e}")

qdrant_client, embedding_model = None, None

def initialize_qdrant_and_embedding():
    global qdrant_client, embedding_model
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    embedding_model = TextEmbedding()

def clean_content(raw_text: str) -> str:
    text = raw_text
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r" +", " ", text)
    return text.strip()

def ask_bh_assurance(query: str):
    query_embedding = list(embedding_model.embed([query]))[0]
    search_response = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=5,
        with_payload=True
    )
    context = ""
    for result in search_response.points:
        payload = result.payload or {}
        content = payload.get('content', '')
        context += clean_content(content) + "\n\n"

    history_text = ""
    if conversation_history:
        history_text = "Previous conversation:\n"
        for i, (q, r) in enumerate(conversation_history):
            history_text += f"Q{i+1}: {q}\nA{i+1}: {r}\n"

    prompt = f"""
You are a friendly, helpful assistant for BH Assurance. Answer user questions conversationally.
{history_text}
User: {query}
Context from documentation:
{context}
"""
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY not set in environment (.env)."
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7
        )
        answer = response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"
    conversation_history.append((query, answer))
    save_conversation_to_file()
    return answer

# ----------------- Neo4j Agent -----------------
class Neo4jAgent:
    # (Include your full Neo4jAgent class implementation here as in your code above)
    # For brevity, assume the class definition is exactly as your current working version
    ...

neo4j_agent = Neo4jAgent(memory_enabled=True)

# ----------------- Query Classification -----------------
def classify_query(query: str) -> str:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
Classify the query into one of two categories:
- "product": about insurance products, general info.
- "client": about specific client data.
Query: {query}
Return only "product" or "client".
"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.0
        )
        category = response.choices[0].message.content.strip().lower()
        if category not in ["product", "client"]:
            category = "product"
        return category
    except Exception:
        return "product"

# ----------------- FastAPI App -----------------
app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.on_event("startup")
async def startup_event():
    initialize_qdrant_and_embedding()

@app.post("/query")
async def process_query(request: QueryRequest):
    query = request.query
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    key = make_cache_key(query)
    cached_response = redis_client.get(key)
    if cached_response:
        return {"response": json.loads(cached_response), "source": "cache"}
    
    category = classify_query(query)
    if category == "product":
        response = ask_bh_assurance(query)
    else:
        response = neo4j_agent.execute_query(query)
    
    redis_client.set(key, json.dumps(response), ex=CACHE_EXPIRATION)
    
    unified_history.append({
        "query": query,
        "response": response,
        "category": category,
        "timestamp": datetime.now().isoformat()
    })
    save_unified_history()
    
    return {"response": response, "source": "backend"}

@app.get("/history")
async def get_history():
    return {"history": unified_history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
