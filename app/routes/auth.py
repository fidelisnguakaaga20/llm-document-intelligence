from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.auth.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


# Hardcoded credentials (as required)
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"


@router.post("/login")
def login(data: LoginRequest):
    if data.username != VALID_USERNAME or data.password != VALID_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": data.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_minutes": 60
    }