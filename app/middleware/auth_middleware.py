from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.services.user_service import UserService
from app.utils.logger import logger
from config import settings

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Verify the JWT token and return the current user
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User: User model instance
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        
        if username is None:
            logger.warning("Token missing username claim")
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"JWT validation error: {str(e)}")
        raise credentials_exception
    
    # Get user from database
    user_service = UserService(db)
    user = user_service.get_user_by_username(username)
    
    if user is None:
        logger.warning(f"User from token not found: {username}")
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Verify that the current user is active
    
    Args:
        current_user: User model instance from get_current_user
        
    Returns:
        User: User model instance
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempt: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Verify that the current user is a superuser (admin)
    
    Args:
        current_user: User model instance from get_current_active_user
        
    Returns:
        User: User model instance
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        logger.warning(f"Non-admin user attempted admin action: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user
