# main.py
import logging
from fastapi import FastAPI
from .controllers import router

app = FastAPI()

# Configuração do log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup():
    logger.info("API iniciada com sucesso!")

@app.on_event("shutdown")
async def shutdown():
    logger.info("API encerrada com sucesso!")

# Incluir as rotas
app.include_router(router)
