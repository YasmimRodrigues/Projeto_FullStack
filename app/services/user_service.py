from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import get_password_hash, verify_password
from app.utils.logger import logger
from app.views.user_schema import UserCreate, UserUpdate

class UserService:
    """Service for user-related operations"""
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get a list of users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Create hashed password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user object
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser
        )
        
        # Add to database
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        logger.info(f"Created new user: {db_user.username}")
        return db_user
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update a user's information"""
        # Get user
        db_user = self.get_user(user_id)
        if not db_user:
            logger.warning(f"Attempted to update non-existent user ID: {user_id}")
            return None
        
        # Update user data
        update_data = user_update.dict(exclude_unset=True)
        
        # Hash password if provided
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # Apply updates
        for key, value in update_data.items():
            setattr(db_user, key, value)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(db_user)
        
        logger.info(f"Updated user: {db_user.username}")
        return db_user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        # Get user
        db_user = self.get_user(user_id)
        if not db_user:
            logger.warning(f"Attempted to delete non-existent user ID: {user_id}")
            return False
        
        # Delete user
        self.db.delete(db_user)
        self.db.commit()
        
        logger.info(f"Deleted user: {db_user.username}")
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        # Get user by username
        user = self.get_user_by_username(username)
        
        # Check if user exists and password is correct
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Failed authentication attempt for username: {username}")
            return None
        
        logger.info(f"User authenticated: {username}")
        return user
    
    def authenticate_user_by_email(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        # Get user by email
        user = self.get_user_by_email(email)
        
        # Check if user exists and password is correct
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Failed authentication attempt for email: {email}")
            return None
        
        logger.info(f"User authenticated with email: {email}")
        return user
