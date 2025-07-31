"""
Supabase client setup and configuration
"""
from typing import Optional
import logging
from app.core.config import settings

# Try to import supabase, handle import errors gracefully
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase client wrapper for authentication and database operations"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client with configuration"""
        try:
            if not SUPABASE_AVAILABLE:
                logger.warning("Supabase library not available. Client not initialized.")
                return
                
            if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
                logger.warning("Supabase configuration is incomplete. Client not initialized.")
                return
            
            # Simple client initialization without extra parameters
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self._client = None
    
    @property
    def client(self) -> Optional[Client]:
        """Get the Supabase client instance"""
        return self._client
    
    def is_connected(self) -> bool:
        """Check if Supabase client is properly initialized"""
        return self._client is not None
    
    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Get user profile from Supabase"""
        if not self._client:
            return None
        
        try:
            response = self._client.table('profiles').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    async def create_user_profile(self, user_id: str, email: str, **kwargs) -> Optional[dict]:
        """Create user profile in Supabase"""
        if not self._client:
            return None
        
        try:
            profile_data = {
                'id': user_id,
                'email': email,
                **kwargs
            }
            response = self._client.table('profiles').insert(profile_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to create user profile: {e}")
            return None
    
    async def verify_user(self, access_token: str) -> Optional[dict]:
        """Verify user authentication with Supabase"""
        if not self._client:
            logger.error("Supabase client not initialized")
            return None
        
        try:
            logger.info(f"Token verification started - Token: {access_token[:20]}...")
            logger.info(f"Supabase URL: {settings.SUPABASE_URL}")
            logger.info(f"Using anon key: {settings.SUPABASE_ANON_KEY[:20]}...")
            
            response = self._client.auth.get_user(access_token)
            
            logger.info(f"Supabase response type: {type(response)}")
            logger.info(f"Response object: {response}")
            
            if response and hasattr(response, 'user') and response.user:
                logger.info(f"User verified successfully: {response.user.email}")
                # ユーザーオブジェクトを辞書形式に変換
                user = response.user
                user_dict = {
                    "sub": user.id,
                    "id": user.id,
                    "email": user.email,
                    "email_verified": user.email_confirmed_at is not None,
                    "app_metadata": user.app_metadata,
                    "user_metadata": user.user_metadata,
                    "role": user.role,
                    "created_at": str(user.created_at) if user.created_at else "",
                    "email_confirmed_at": str(user.email_confirmed_at) if user.email_confirmed_at else ""
                }
                logger.info(f"Returning user dict: {user_dict}")
                return user_dict
            else:
                logger.warning(f"Token verification returned no user - Response: {response}")
                return None
        except Exception as e:
            logger.error(f"Failed to verify user with token {access_token[:10]}...: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception details: {str(e)}")
            return None

# Global instance
supabase_client = SupabaseClient()