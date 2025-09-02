from fastapi import APIRouter, Depends, HTTPException
from middleware.jwt_verifier import verify_jwt
from databases import Database
from pydantic import BaseModel

router = APIRouter()


class ContactMessage(BaseModel):
    sujet: str = None  # Optional subject
    message: str

def get_user_router(database: Database):
    @router.post("/contact")
    async def create_contact_message(
        contact_data: ContactMessage,
        payload: dict = Depends(verify_jwt)
    ):
        """
        Creates a new contact message from the authenticated user.
        Requires JWT authentication and expects sujet (optional) and message in the request body.
        """
        user_id = int(payload["sub"])  # assuming 'sub' in JWT contains user ID
        
        # Validate that message is not empty
        if not contact_data.message or not contact_data.message.strip():
            raise HTTPException(status_code=400, detail="Le message ne peut pas être vide")
        
        try:
            query = """
            INSERT INTO messages (user_id, sujet, message)
            VALUES (:user_id, :sujet, :message)
            RETURNING id, created_at
            """
            
            result = await database.fetch_one(
                query=query,
                values={
                    "user_id": user_id,
                    "sujet": contact_data.sujet,
                    "message": contact_data.message.strip()
                }
            )
            
            return {
                "success": True,
                "message": "Votre message a été envoyé avec succès",
                "id": result["id"],
                "created_at": result["created_at"]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi du message")
    @router.get("/user/profile")
    async def get_user_profile(payload: dict = Depends(verify_jwt)):
        """
        Returns the user's profile information (username and email)
        based on the JWT token.
        """
        user_id = int(payload["sub"])  # assuming 'sub' in JWT contains user ID

        query = """
        SELECT username, email
        FROM users
        WHERE id = :user_id
        """
        user = await database.fetch_one(query=query, values={"user_id": user_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "username": user["username"],
            "email": user["email"]
        }

    return router
