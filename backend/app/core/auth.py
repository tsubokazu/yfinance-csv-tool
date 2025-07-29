"""
Authentication middleware and utilities for FastAPI + Supabase
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.supabase_client import supabase_client
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()

class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from Supabase
    """
    try:
        if not credentials:
            raise AuthenticationError("No authentication credentials provided")
        
        token = credentials.credentials
        if not token:
            raise AuthenticationError("Invalid authentication token")
        
        # Verify token with Supabase
        user = await supabase_client.verify_user(token)
        if not user:
            raise AuthenticationError("Invalid or expired token")
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise AuthenticationError("Authentication verification failed")

async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Optional[Dict[str, Any]]:
    """
    Dependency to get current user's profile from database
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            return None
        
        profile = await supabase_client.get_user_profile(user_id)
        return profile
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        return None

async def get_optional_current_user(
    request: Request
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns user if authenticated, None otherwise
    """
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        user = await supabase_client.verify_user(token)
        return user
        
    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
        return None

def require_roles(*roles: str):
    """
    Decorator to require specific roles for endpoint access
    """
    def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_roles = current_user.get('app_metadata', {}).get('roles', [])
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {list(roles)}"
            )
        return current_user
    
    return role_checker

async def create_user_session(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Create user session with email/password
    """
    try:
        if not supabase_client.client:
            raise Exception("Supabase client not initialized")
        
        response = supabase_client.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": response.user
        }
        
    except Exception as e:
        logger.error(f"Failed to create user session: {e}")
        return None

async def register_user(email: str, password: str, **metadata) -> Optional[Dict[str, Any]]:
    """
    Register new user with email/password
    """
    try:
        if not supabase_client.client:
            raise Exception("Supabase client not initialized")
        
        response = supabase_client.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": metadata
            }
        })
        
        return {
            "user": response.user,
            "session": response.session
        }
        
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        return None