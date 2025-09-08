from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from databases import Database
from final_agent import classify_query, ask_bh_assurance, summarize_text
from typing import Optional
import json
import uuid
import hashlib
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
security = HTTPBearer()

class QueryRequest(BaseModel):
    query: str
    chat_id: int | None = None

def get_query_router(redis_client, embedding_model, neo4j_agent, database: Database, CACHE_TTL_SECONDS: int):
    router = APIRouter()

    @router.post("/query")
    async def process_query(request: QueryRequest, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
        query_text = request.query.strip()
        if not query_text:
            return {"response": "Query is required", "chat_id": None}

        payload = None
        if credentials:
            token = credentials.credentials
            if token.lower().startswith("bearer "):
                token = token[7:]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                payload = None
            except jwt.InvalidTokenError:
                payload = None

        category = classify_query(query_text)
        user_id: Optional[int] = None
        final_chat_id: Optional[int] = None

        # ------------------- Authenticated users -------------------
        if payload:
            user_id = int(payload["sub"])

            # Determine chat room
            final_chat_id = request.chat_id
            if not final_chat_id:
                chat_name = await summarize_text(query_text)
                final_chat_id = await database.execute(
                    "INSERT INTO chats (user_id, name, created_at) VALUES (:user_id, :name, NOW()) RETURNING id",
                    values={"user_id": user_id, "name": chat_name}
                )

            # Response logic
            if category == "client":
                query_user = "SELECT cin, matricule_fiscale FROM users WHERE id = :user_id"
                user_data = await database.fetch_one(query=query_user, values={"user_id": user_id})
                if not user_data:
                    return {"response": "User not found", "chat_id": final_chat_id}

                user_identifier = user_data["matricule_fiscale"] or user_data["cin"]
                if not user_identifier:
                    return {"response": "User has no CIN or matricule_fiscale", "chat_id": final_chat_id}

                response = neo4j_agent.execute_query(query_text, user_identifier)
            else:
                cached_response = await redis_client.get(query_text)
                if cached_response:
                    response = json.loads(cached_response)
                else:
                    response = ask_bh_assurance(query_text, embedding_model)
                    await redis_client.setex(query_text, CACHE_TTL_SECONDS, json.dumps(response))

        # ------------------- Visitor users -------------------
        else:
            visitor_user = await database.fetch_one("SELECT id FROM users WHERE full_name = 'visitor'")
            if not visitor_user:
                visitor_id = await database.execute(
                    """
                    INSERT INTO users (full_name, email, password_hash, cin, matricule_fiscale)
                    VALUES (:full_name, :email, :password_hash, :cin, NULL) RETURNING id
                    """,
                    values={
                        "full_name": "visitor",
                        "email": f"visitor_{uuid.uuid4().hex[:8]}@bh.com",
                        "password_hash": hashlib.sha256(uuid.uuid4().hex.encode()).hexdigest(),
                        "cin": f"VIS{uuid.uuid4().hex[:6]}"
                    }
                )
            else:
                visitor_id = visitor_user["id"]

            user_id = visitor_id
            visitor_chat = await database.fetch_one("SELECT id FROM chats WHERE user_id = :uid AND name = 'visitor room'", values={"uid": visitor_id})
            final_chat_id = visitor_chat["id"] if visitor_chat else await database.execute(
                "INSERT INTO chats (user_id, name, created_at) VALUES (:uid, 'visitor room', NOW()) RETURNING id",
                values={"uid": visitor_id}
            )

            # Visitors always use BH Assurance
            response = ask_bh_assurance(query_text, embedding_model)

        # ------------------- Save conversation -------------------
        if user_id and final_chat_id:
            await database.execute(
                """
                INSERT INTO conversations(chat_id, query, response, category, timestamp)
                VALUES (:chat_id, :query, :response, :category, NOW())
                """,
                values={
                    "chat_id": final_chat_id,
                    "query": query_text,
                    "response": json.dumps(response),
                    "category": category
                }
            )

        return {"response": response, "chat_id": final_chat_id}

    return router

