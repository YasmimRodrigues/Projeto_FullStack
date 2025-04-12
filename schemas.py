# schemas.py
from pydantic import BaseModel

class UserCreate(BaseModel):  # Changed from UsuarioCriar
    username: str            # Changed from nome_usuario
    email: str
    password: str           # Changed from senha

class UserUpdate(BaseModel):  # Changed from UsuarioAtualizar
    username: str | None = None      # Changed from nome_usuario
    email: str | None = None
    password: str | None = None      # Changed from senha

class UserResponse(BaseModel):  # Changed from UsuarioResposta
    id: int
    username: str           # Changed from nome_usuario
    email: str
    access_token: str       # Changed from token_acesso
    token_type: str         # Changed from tipo_token

    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2
