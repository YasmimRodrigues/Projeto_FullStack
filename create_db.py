# create_db.py
from app.database import engine
from app import models

# Criar todas as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)
