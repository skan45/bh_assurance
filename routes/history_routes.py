from fastapi import APIRouter, Depends, HTTPException
from middleware.jwt_verifier import verify_jwt
from databases import Database
from typing import List, Dict

router = APIRouter()

def get_user_chats_router(database: Database):
    # Route 1: Get all chat names with IDs
    @router.get("/user_chats")
    async def get_user_chats(payload: dict = Depends(verify_jwt)):
        user_id = int(payload["sub"])
        query = "SELECT id AS chat_id, name AS chat_name FROM chats WHERE user_id = :user_id ORDER BY id"
        chats = await database.fetch_all(query=query, values={"user_id": user_id})
        return {"chats": [{"chat_id": chat["chat_id"], "chat_name": chat["chat_name"]} for chat in chats]}

    # Route 2: Get all conversations for a specific chat
    @router.get("/chat/{chat_id}/conversations")
    async def get_chat_conversations(chat_id: int, payload: dict = Depends(verify_jwt)):
        user_id = int(payload["sub"])
        # Verify chat belongs to user
        chat_query = "SELECT id FROM chats WHERE id = :chat_id AND user_id = :user_id"
        chat = await database.fetch_one(query=chat_query, values={"chat_id": chat_id, "user_id": user_id})
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        conv_query = """
        SELECT id, query, response, category, timestamp
        FROM conversations
        WHERE chat_id = :chat_id
        ORDER BY timestamp
        """
        conversations = await database.fetch_all(query=conv_query, values={"chat_id": chat_id})
        return {"conversations": [
            {
                "id": conv["id"],
                "query": conv["query"],
                "response": conv["response"],
                "category": conv["category"],
                "timestamp": conv["timestamp"]
            } for conv in conversations
        ]}

    return router

