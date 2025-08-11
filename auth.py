from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse
from typing import Optional
import database
from functools import wraps

class AuthMiddleware:
    @staticmethod
    def get_current_user(request: Request) -> Optional[dict]:
        """Get current user from session cookie"""
        session_id = request.cookies.get("session_id")
        if not session_id:
            return None
        
        user = database.get_session_user(session_id)
        return user
    
    @staticmethod
    def is_authenticated(request: Request) -> bool:
        """Check if user is authenticated"""
        return AuthMiddleware.get_current_user(request) is not None
    
    @staticmethod
    def is_admin(request: Request) -> bool:
        """Check if user is an admin"""
        user = AuthMiddleware.get_current_user(request)
        return user is not None and user.get('is_admin', False)
    
    @staticmethod
    def require_auth(request: Request):
        """Require authentication, raise HTTPException if not authenticated"""
        if not AuthMiddleware.is_authenticated(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
    
    @staticmethod
    def require_admin(request: Request):
        """Require admin access, raise HTTPException if not admin"""
        if not AuthMiddleware.is_authenticated(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not AuthMiddleware.is_admin(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

def require_auth(func):
    """Decorator to require authentication for endpoints"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        AuthMiddleware.require_auth(request)
        return await func(request, *args, **kwargs)
    return wrapper

def require_admin(func):
    """Decorator to require admin access for endpoints"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        AuthMiddleware.require_admin(request)
        return await func(request, *args, **kwargs)
    return wrapper

def get_user(request: Request) -> Optional[dict]:
    """Helper function to get current user"""
    return AuthMiddleware.get_current_user(request)