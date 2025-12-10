from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth import decode_access_token
from typing import Optional

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials) -> dict:
    """Validate JWT token and return user data"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    email: str = payload.get('sub')
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials'
        )
    
    return {'email': email, 'role': payload.get('role', 'admin')}


async def require_admin(request: Request):
    """Middleware to require admin authentication"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated'
        )
    
    token = auth_header.split(' ')[1]
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token'
        )
    
    request.state.user = payload
    return payload
