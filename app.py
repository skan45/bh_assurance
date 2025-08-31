from fastapi import FastAPI
from redis.asyncio import Redis
from dotenv import load_dotenv
import os
from final_agent import initialize_embedding_model, Neo4jAgent
from routes.query_routes import get_query_router
from routes.auth_routes import get_auth_router
from routes.history_routes import get_user_chats_router
from database import database
from pydantic import BaseModel
from routes.devis_route  import router as devis_router

load_dotenv()
# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = int(os.getenv("REDIS_PORT",6379 ))
REDIS_DB = int(os.getenv("REDIS_DB",0 ))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 3600 ))

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
redis_client: Redis = None
embedding_model = None
neo4j_agent = None
@app.on_event("startup")
async def startup_event():
    global embedding_model, neo4j_agent , redis_client
    embedding_model = initialize_embedding_model()
    await database.connect()
    neo4j_agent = Neo4jAgent(memory_enabled=True)
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    query_router = get_query_router(
        redis_client=redis_client,
        embedding_model=embedding_model,
        neo4j_agent=neo4j_agent,
        database=database,
        CACHE_TTL_SECONDS=CACHE_TTL_SECONDS)
    app.include_router(query_router, prefix="/api")
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    neo4j_agent.close()
    
history_router=get_user_chats_router(database)
auth_router = get_auth_router(database)
app.include_router(history_router, prefix="/api/history")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(devis_router, prefix="/api")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")

