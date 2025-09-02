from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from final_agent import classify_query, ask_bh_assurance, summarize_text  # <- assume you have a function that calls OpenAI
import json, re
from middleware.jwt_verifier import verify_jwt
from databases import Database
from datetime import datetime

last_client_ref = None
last_client_matricule = None

class QueryRequest(BaseModel):
    query: str
    chat_id: int | None = None  # optional, for existing chats

def get_query_router(redis_client, embedding_model, neo4j_agent, database: Database, CACHE_TTL_SECONDS: int):
    router = APIRouter()

    @router.post("/query")
    async def process_query(request: QueryRequest, payload: dict = Depends(verify_jwt)):
        global last_client_ref, last_client_matricule

        user_id = int(payload["sub"])
        query_text = request.query.strip()
        if not query_text:
            raise HTTPException(status_code=400, detail="Query is required")

        # --- Redis cache ---
        cached_response = await redis_client.get(query_text)
        if cached_response:
            return {"response": json.loads(cached_response)}

        # --- Extract context ---
        match_ref = re.search(r"client\s*(\d+)", query_text)
        match_mat = re.search(r"matricule\s*fiscale\s*(?:est|=|:)?\s*(\w+)", query_text)

        if match_mat:
            last_client_matricule = match_mat.group(1)
            neo4j_agent._conversation["person_matricule"] = last_client_matricule
        elif match_ref:
            last_client_ref = match_ref.group(1)
            neo4j_agent._conversation["person_ref"] = last_client_ref

        # --- Add context for processing ---
        query_for_agent = query_text
        if last_client_matricule and "matricule_fiscale" not in query_for_agent:
            query_for_agent += f" (matricule fiscale est {last_client_matricule})"
        elif last_client_ref and "ref_personne" not in query_for_agent:
            query_for_agent += f" (ref_personne est {last_client_ref})"

        # --- Classify and get response ---
        category = await  classify_query(query_for_agent)
        if category == "product":
            response = await  ask_bh_assurance(query_for_agent, embedding_model)
        else:
            response = neo4j_agent.execute_query(query_for_agent)

        # --- Store in Redis ---
        await redis_client.setex(query_text, CACHE_TTL_SECONDS, json.dumps(response))

        # --- Handle chat ---
        chat_id = request.chat_id
        if not chat_id:
            # Generate chat name using the first query
            chat_name = await summarize_text(query_text)  # e.g., call OpenAI API to summarize
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

