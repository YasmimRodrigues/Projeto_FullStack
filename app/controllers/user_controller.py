from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.middleware.auth_middleware import get_current_active_user, get_current_superuser
from app.models.user import User
from app.services.user_service import UserService
from app.utils.logger import logger
from app.views.user_schema import UserRead, UserUpdate, UserCreate

router = APIRouter()

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get information about the currently authenticated user"""
    logger.info(f"User {current_user.username} accessing their information")
    return current_user

@router.put("/me", response_model=UserRead)
async def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update the currently authenticated user's information"""
    logger.info(f"User {current_user.username} updating their information")
    
    user_service = UserService(db)
    updated_user = user_service.update_user(current_user.id, user_update)
    
    if not updated_user:
        logger.error(f"Failed to update user {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    logger.info(f"User {current_user.username} updated successfully")
    return updated_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete the currently authenticated user"""
    logger.info(f"User {current_user.username} requested account deletion")
    
    user_service = UserService(db)
    success = user_service.delete_user(current_user.id)
    
    if not success:
        logger.error(f"Failed to delete user {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    
    logger.info(f"User {current_user.username} deleted successfully")
    return {"detail": "User deleted successfully"}

# Admin routes (requires superuser)
@router.get("/", response_model=List[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Get a list of all users (admin only)"""
    logger.info(f"Admin {current_user.username} accessing list of users")
    
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit)
    
    return users

@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Get a specific user by ID (admin only)"""
    logger.info(f"Admin {current_user.username} accessing user with ID {user_id}")
    
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    
    if not user:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Update a specific user by ID (admin only)"""
    logger.info(f"Admin {current_user.username} updating user with ID {user_id}")
    
    user_service = UserService(db)
    updated_user = user_service.update_user(user_id, user_update)
    
    if not updated_user:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User with ID {user_id} updated successfully by admin {current_user.username}")
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Delete a specific user by ID (admin only)"""
    logger.info(f"Admin {current_user.username} deleting user with ID {user_id}")
    
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    
    if not success:
        logger.warning(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User with ID {user_id} deleted successfully by admin {current_user.username}")
    return {"detail": "User deleted successfully"}

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Create a new user (admin only)"""
    logger.info(f"Admin {current_user.username} creating new user with username: {user_data.username}")
    
    user_service = UserService(db)
    
    # Check if username already exists
    if user_service.get_user_by_username(user_data.username):
        logger.warning(f"User creation failed: Username {user_data.username} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if user_service.get_user_by_email(user_data.email):
        logger.warning(f"User creation failed: Email {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = user_service.create_user(user_data)
    logger.info(f"User {user.username} created successfully by admin {current_user.username}")
    
    return user
