import bcrypt
import jwt
from middleware.cin_verifier import check_input
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from databases import Database
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional
import os

load_dotenv()

# --- Models ---
class UserRegister(BaseModel):
    full_name: str
    password: str
    email: EmailStr
    cin: Optional[str] = None
    matricule_fiscale: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- JWT Settings ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM = "HS256"

# --- Auth Router ---
def get_auth_router(database: Database):
    router = APIRouter()

    @router.post("/register")
    async def register(user: UserRegister):
    # Check that at least CIN or matricule_fiscale is provided
     if not user.cin and not user.matricule_fiscale:
        raise HTTPException(status_code=400, detail="CIN or Matricule Fiscale must be provided")

    # Always call check_input for each provided field
     if user.cin:
        if not check_input(user.cin):
            raise HTTPException(status_code=400, detail="CIN not found in external database")
     
     if user.matricule_fiscale:
        if not check_input(user.matricule_fiscale):
            raise HTTPException(status_code=400, detail="Matricule Fiscale not found in external database")

    # Check if email already exists
     query = "SELECT * FROM users WHERE email = :email"
     existing = await database.fetch_one(query=query, values={"email": user.email})
     if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash password
     hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode()

    # Insert user
     insert_query = """
    INSERT INTO users(full_name, email, password_hash, cin, matricule_fiscale)
    VALUES(:full_name, :email, :password_hash, :cin, :matricule_fiscale)
    """
     await database.execute(
        query=insert_query,
        values={
            "full_name": user.full_name,
            "email": user.email,
            "password_hash": hashed_pw,
            "cin": user.cin,
            "matricule_fiscale": user.matricule_fiscale
        }
    )
     return {"message": "User registered successfully"}


    @router.post("/login")
    async def login(user: UserLogin):
        query = "SELECT * FROM users WHERE email = :email"
        db_user = await database.fetch_one(query=query, values={"email": user.email})
        if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password_hash"].encode("utf-8")):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        # --- Create JWT Token ---
        expire = datetime.utcnow() + timedelta(minutes=60)
        payload = {
            "sub": str(db_user["id"]),
            "email": db_user["email"],
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

