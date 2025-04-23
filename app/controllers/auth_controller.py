from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.user_service import UserService
from app.utils.logger import logger
from app.utils.security import create_access_token
from app.views.auth_schema import Token, UserCreate, UserLogin

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return an access token"""
    logger.info(f"Registering new user with username: {user_data.username}")
    
    user_service = UserService(db)
    
    # Check if username already exists
    if user_service.get_user_by_username(user_data.username):
        logger.warning(f"Registration failed: Username {user_data.username} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if user_service.get_user_by_email(user_data.email):
        logger.warning(f"Registration failed: Email {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = user_service.create_user(user_data)
    
    # Generate access token
    access_token = create_access_token(data={"sub": user.username})
    
    logger.info(f"User {user.username} registered successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate a user and return an access token"""
    logger.info(f"Login attempt for user: {form_data.username}")
    
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate access token
    access_token = create_access_token(data={"sub": user.username})
    
    logger.info(f"User {user.username} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/email", response_model=Token)
async def login_with_email(user_login: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user with email and password and return an access token"""
    logger.info(f"Login attempt with email: {user_login.email}")
    
    user_service = UserService(db)
    user = user_service.authenticate_user_by_email(user_login.email, user_login.password)
    
    if not user:
        logger.warning(f"Login failed for email: {user_login.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate access token
    access_token = create_access_token(data={"sub": user.username})
    
    logger.info(f"User with email {user_login.email} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}
