from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
# [MOCK] from app.database.session import get_db
# [MOCK] from app.core.redis_client import redis_client
from app.auth.password import get_password_hash, verify_password
from app.auth.jwt_handler import create_access_token, create_refresh_token, verify_token, get_current_user
import uuid

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class RegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class RefreshSchema(BaseModel):
    refresh_token: str

@router.post("/register")
def register(user: RegisterSchema):
    # Validate: email format, password min 8 chars, username unique
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 chars")
    
    # [MOCK] check unique username/email in DB
    
    # Hash password: bcrypt with 12 rounds
    hashed_pw = get_password_hash(user.password)
    
    # Create User DB record
    user_id = str(uuid.uuid4())
    
    # issue JWT pair (access + refresh)
    access_token = create_access_token({"sub": user_id, "role": "user"})
    refresh_token = create_refresh_token({"sub": user_id, "role": "user"})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": user_id,
        "username": user.username
    }

@router.post("/login")
def login(creds: LoginSchema):
    # Verify password hash, check account not banned
    # [MOCK] fetch user by email
    mock_user_id = str(uuid.uuid4())
    mock_user_pw_hash = get_password_hash("password123") # mock hash
    
    if not mock_user_pw_hash or not verify_password(creds.password, mock_user_pw_hash):
        if creds.password != "password123": # allow mockup to pass if matching
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    # Issue new JWT pair
    access_token = create_access_token({"sub": mock_user_id, "role": "user"})
    refresh_token = create_refresh_token({"sub": mock_user_id, "role": "user"})
    
    # Store refresh_token hash in Redis: SET auth:refresh:{user_id} {token_hash} EX 604800
    # [MOCK] redis_client.setex(f"auth:refresh:{mock_user_id}", 604800, get_password_hash(refresh_token))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@router.post("/refresh")
def refresh(data: RefreshSchema):
    # Verify token, check Redis for validity
    payload = verify_token(data.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user_id = payload.get("sub")
    
    # Issue new access_token (15 min expiry)
    access_token = create_access_token({"sub": user_id, "role": payload.get("role", "user")})
    
    # Rotate refresh_token (issue new, invalidate old in Redis)
    new_refresh_token = create_refresh_token({"sub": user_id, "role": payload.get("role", "user")})
    # [MOCK] redis_client.setex(f"auth:refresh:{user_id}", 604800, get_password_hash(new_refresh_token))
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token
    }

@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)): # Simplified Depends
    if current_user and "sub" in current_user:
        user_id = current_user["sub"]
        # Invalidate refresh_token in Redis
        # [MOCK] redis_client.delete(f"auth:refresh:{user_id}")
    return {"message": "Logged out"}
