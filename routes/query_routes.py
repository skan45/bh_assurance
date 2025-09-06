from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from final_agent import classify_query, ask_bh_assurance, summarize_text
import json
from middleware.jwt_verifier import verify_jwt
from databases import Database

class QueryRequest(BaseModel):
    query: str
    chat_id: int | None = None  # optional, for existing chats

def get_query_router(redis_client, embedding_model, neo4j_agent, database: Database, CACHE_TTL_SECONDS: int):
    router = APIRouter()

    @router.post("/query")
    async def process_query(request: QueryRequest,payload: dict = Depends(verify_jwt)):
         
        
        user_id = int(payload["sub"])
        query_text = request.query.strip()
        if not query_text:
            raise HTTPException(status_code=400, detail="Query is required")

        # --- Fetch CIN / matricule_fiscale from DB ---
        query_user = "SELECT cin, matricule_fiscale FROM users WHERE id = :user_id"
        user_data = await database.fetch_one(query=query_user, values={"user_id": user_id})
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        user_identifier = user_data["matricule_fiscale"] or user_data["cin"]

        if not user_identifier:
            raise HTTPException(status_code=400, detail="User has no CIN or matricule_fiscale registered")

        # --- Redis cache ---
        cached_response = await redis_client.get(query_text)
        if cached_response:
            return {"response": json.loads(cached_response)}

        # --- Classify and get response ---
        category = await classify_query(query_text)
        if category == "product":
            response = await ask_bh_assurance(query_text, embedding_model)
        else:
            response = await neo4j_agent.execute_query(query_text, user_identifier)

        # --- Store in Redis ---
        await redis_client.setex(query_text, CACHE_TTL_SECONDS, json.dumps(response))

        # --- Handle chat ---
        chat_id = request.chat_id
        if not chat_id:
            chat_name = await summarize_text(query_text)
            insert_chat = """
            INSERT INTO chats(user_id, name, created_at)
            VALUES (:user_id, :name, NOW())
            RETURNING id
            """
            chat_id = await database.execute(query=insert_chat, values={"user_id": user_id, "name": chat_name})

        # --- Save to PostgreSQL ---
        insert_conversation = """
        INSERT INTO conversations(chat_id, query, response, category, timestamp)
        VALUES (:chat_id, :query, :response, :category, NOW())
        """
        await database.execute(
            query=insert_conversation,
            values={
                "chat_id": chat_id,
                "query": query_text,
                "response": json.dumps(response),
                "category": category
            }
        )

        return {"response": response, "chat_id": chat_id}

    return router

