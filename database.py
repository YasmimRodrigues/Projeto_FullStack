# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter a URL de conexão do PostgreSQL
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "postgresql+psycopg2://postgres:b2b6e2d0afa36e3adea8@marinho_backpython:5432/marinho")

# Configurar o motor do SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={})

# Configurar o SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base para os modelos
Base = declarative_base()

# Função para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
