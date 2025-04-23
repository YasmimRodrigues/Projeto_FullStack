from pydantic import BaseModel, EmailStr, Field, validator

class UserBase(BaseModel):
    """Base schema for user data"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """Schema for user creation request"""
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

class UserLogin(BaseModel):
    """Schema for user login with email"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str
