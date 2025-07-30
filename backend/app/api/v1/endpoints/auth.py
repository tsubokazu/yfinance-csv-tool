"""
Authentication API endpoints
"""
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.core.auth import (
    create_user_session,
    register_user,
    get_current_user,
    get_current_user_profile
)
from app.core.supabase_client import supabase_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Request models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    username: str = ""

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str = ""
    username: str = ""
    created_at: str
    email_confirmed_at: str = ""

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> Dict[str, Any]:
    """
    User login with email and password
    """
    try:
        session_data = await create_user_session(
            email=request.email,
            password=request.password
        )
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_data = session_data["user"]
        return {
            "access_token": session_data["access_token"],
            "token_type": "bearer",
            "user": {
                "id": user_data.id,
                "email": user_data.email,
                "full_name": user_data.user_metadata.get("full_name", ""),
                "username": user_data.user_metadata.get("username", ""),
                "created_at": str(user_data.created_at),
                "email_confirmed_at": str(user_data.email_confirmed_at) if user_data.email_confirmed_at else ""
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest) -> Dict[str, Any]:
    """
    User registration with email and password
    """
    try:
        registration_data = await register_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            username=request.username
        )
        
        if not registration_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        
        user_data = registration_data["user"]
        session_data = registration_data["session"]
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration successful but login failed"
            )
        
        return {
            "access_token": session_data.access_token,
            "token_type": "bearer",
            "user": {
                "id": user_data.id,
                "email": user_data.email,
                "full_name": user_data.user_metadata.get("full_name", ""),
                "username": user_data.user_metadata.get("username", ""),
                "created_at": str(user_data.created_at),
                "email_confirmed_at": str(user_data.email_confirmed_at) if user_data.email_confirmed_at else ""
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user information
    """
    try:
        return {
            "id": current_user.get("sub", current_user.get("id", "")),
            "email": current_user.get("email", ""),
            "full_name": current_user.get("user_metadata", {}).get("full_name", ""),
            "username": current_user.get("user_metadata", {}).get("username", ""),
            "created_at": current_user.get("created_at", ""),
            "email_confirmed_at": current_user.get("email_confirmed_at", "")
        }
        
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.get("/profile")
async def get_profile(
    profile: Dict[str, Any] = Depends(get_current_user_profile)
) -> Dict[str, Any]:
    """
    Get current user profile from database
    """
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return profile

@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    User logout (invalidate session)
    """
    try:
        if supabase_client.client:
            supabase_client.client.auth.sign_out()
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/status")
async def auth_status() -> Dict[str, Any]:
    """
    Check authentication service status
    """
    return {
        "status": "active",
        "supabase_connected": supabase_client.is_connected(),
        "service": "Supabase Authentication"
    }