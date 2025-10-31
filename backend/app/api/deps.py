"""API dependencies."""

from typing import Optional
from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key if authentication is enabled."""
    if not settings.ENABLE_API_KEY_AUTH:
        return True
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Implement your API key validation logic here
    # For now, just a placeholder
    valid_keys = []  # Load from database or config
    
    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True
