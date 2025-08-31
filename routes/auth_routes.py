import bcrypt
import jwt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel,EmailStr
from databases import Database
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
import os

load_dotenv()
# --- Models ---
class UserRegister(BaseModel):
    username: str
    password: str
    email: EmailStr
    ref_person: Optional[int] = None
    matricule_fiscale: Optional[int] = None

class UserLogin(BaseModel):
    username: str
    password: str

# --- JWT Settings ---

SECRET_KEY = os.getenv("JWT_SECRET_KEY","")
ALGORITHM = "HS256"

# --- Auth Router ---
def get_auth_router(database: Database):
    router = APIRouter()

    @router.post("/register")
    async def register(user: UserRegister):
        query = "SELECT * FROM users WHERE username = :username OR email = :email"
        existing = await database.fetch_one(query=query, values={"username": user.username, "email":user.email})
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")

        hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode()
        insert_query = "INSERT INTO users(username, password_hash, email, ref_person, matricule_fiscale) VALUES(:username, :password_hash, :email, :ref_person, :matricule_fiscale )"
        await database.execute(query=insert_query, values={"username": user.username, "password_hash": hashed_pw, "email":user.email, "ref_person":user.ref_person,"matricule_fiscale":user.matricule_fiscale})
        return {"message": "User registered successfully"}

    @router.post("/login")
    async def login(user: UserLogin):
        query = "SELECT * FROM users WHERE username = :username"
        db_user = await database.fetch_one(query=query, values={"username": user.username})
        if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password_hash"].encode("utf-8")):
            raise HTTPException(status_code=400, detail="Invalid username or password")

        # --- Create JWT Token ---
        expire = datetime.utcnow() + timedelta(minutes=60)
        payload = {
            "sub": str(db_user["id"]),
            "username": db_user["username"],
            "exp": expire
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return {
            "message": "Login successful",
            "user_id": db_user["id"],
            "access_token": token,
            "token_type": "bearer"
        }

    return router

