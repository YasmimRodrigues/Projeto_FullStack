from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator

class UserBase(BaseModel):
    """Base schema for user data"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=8)
    is_active: bool = True
    is_superuser: bool = False
    
    @validator('password')
    def password_complexity(cls, v):
        """Validate password complexity"""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserUpdate(BaseModel):
    """Schema for user update"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    
    @validator('password')
    def password_complexity(cls, v):
        """Validate password complexity if password is provided"""
        if v is None:
            return v
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserRead(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
