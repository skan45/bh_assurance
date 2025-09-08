from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
import os
from typing import Optional

SECRET_KEY = os.getenv("SECRET_KEY", "")
security = HTTPBearer(auto_error=False)  # <-- allow missing token

async def get_optional_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Extract JWT payload if a valid token is provided.
    Returns None if token is missing or invalid.
    """
    if not credentials:
        return None  # no token sent

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

