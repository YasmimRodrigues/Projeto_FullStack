# models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True)



class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    access_token: str
    token_type: str

    # Certifique-se de adicionar orm_mode = True se estiver utilizando o SQLAlchemy
    class Config:
        orm_mode = True  # Isso permite que o Pydantic use objetos SQLAlchemy diretamente
