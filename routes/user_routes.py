from fastapi import APIRouter, Depends, HTTPException
from middleware.jwt_verifier import verify_jwt
from databases import Database

router = APIRouter()

def get_user_router(database: Database):
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