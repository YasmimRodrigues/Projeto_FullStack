from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging
import json
import os
from datetime import datetime
import time
from . import schemas, models, security
from .database import get_db
from typing import Optional

# Configuração do logger JSON
class ContextualLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs["extra"] = self.extra
        return msg, kwargs

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record ={
        "data_hora": datetime.fromtimestamp(record.created).isoformat(),
        "nivel": record.levelname,
        "detail": record.getMessage(),
        "registrador": record.name,
        "caminho": record.pathname,
        "funcao": record.funcName,
        "linha": record.lineno,
        "id_usuario": getattr(record, 'user_id', None),
        "nome_usuario": getattr(record, 'username', None),
        "acao": getattr(record, 'action', None),
        "id_alvo": getattr(record, 'target_id', None),
        "ip_cliente": getattr(record, 'client_ip', None)
        }


        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("api_fullstack")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/api.log")
file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(JSONFormatter())
logger.addHandler(console_handler)

def get_logger(action: str, user: Optional[models.User] = None, target_id: Optional[int] = None):
    extra = {
        "acao": action,
        "id_usuario": user.id if user else None,
        "nome_usuario": user.username if user else None,
        "id_alvo": target_id
    }

    return ContextualLogger(logger, extra)

# Middleware de segurança
bearer_scheme = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/api/v1",
    tags=["API Fullstack FAPAM"],
    responses={
        401: {"description": "Não autorizado"},
        403: {"description": "Acesso proibido"},
        500: {"description": "Erro interno"}
    }
)

def handle_db_exception(logger, e, operation: str):
    logger.error(f"Erro de banco de dados durante {operation}: {str(e)}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro durante operação de {operation}"
    )

@router.post("/usuarios/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: schemas.UserCreate, db: Session = Depends(get_db)):
    action_logger = get_logger("criar_usuario")
    try:
        action_logger.info(f"Iniciando criação de usuário: {usuario.username}")
        
        # Validações
        db_usuario = db.query(models.User).filter(models.User.username == usuario.username).first()
        if db_usuario:
            action_logger.warning("Nome de usuário já existe")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome de usuário já existe"
            )

        db_email = db.query(models.User).filter(models.User.email == usuario.email).first()
        if db_email:
            action_logger.warning("Email já registrado")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já registrado"
            )

        senha_criptografada = security.get_password_hash(usuario.password)
        
        try:
            novo_usuario = models.User(
                username=usuario.username,
                password=senha_criptografada,
                email=usuario.email
            )
            db.add(novo_usuario)
            db.commit()
            db.refresh(novo_usuario)
        except Exception as e:
            handle_db_exception(action_logger, e, "criação de usuário")

        action_logger.info("Usuário criado com sucesso")
        
        token_acesso = security.create_access_token(data={"sub": novo_usuario.username})
        
        return {
        "id": novo_usuario.id,
        "username": novo_usuario.username,  # Changed from nome_usuario
        "email": novo_usuario.email,
        "access_token": token_acesso,      # Changed from token_acesso
        "token_type": "bearer"             # Changed from tipo_token
    }




    except HTTPException as he:
        raise he
    except Exception as e:
        action_logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar requisição"
        )

@router.post("/token", response_model=schemas.UserResponse)
def login_para_token_acesso(dados_formulario: schemas.UserCreate, db: Session = Depends(get_db)):
    action_logger = get_logger("login")
    try:
        action_logger.info(f"Tentativa de login: {dados_formulario.username}")
        
        try:
            usuario = security.authenticate_user(db, dados_formulario.username, dados_formulario.password)
        except Exception as e:
            handle_db_exception(action_logger, e, "autenticação")

        if not usuario:
            action_logger.warning("Credenciais inválidas")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_acesso = security.create_access_token(data={"sub": username})
        
        action_logger.info("Login bem-sucedido")
        return{
        "id": id,
        "nome_usuario":username,
        "email": email,
        "token_acesso": token_acesso,
        "tipo_token": "bearer"
    }


    except HTTPException as he:
        raise he
    except Exception as e:
        action_logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro durante o processo de login"
        )

def obter_usuario_atual(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        if not token:
            logger.warning("Tentativa de acesso sem token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de acesso necessário"
            )

        usuario = security.get_current_user(db, token)
        logger.info(f"Usuário autenticado: {usuario.username}", extra={
            "user_id": usuario.id,
            "username": usuario.username,
            "action": "autenticação"
        })
        return usuario
    except HTTPException as he:
        logger.error(f"Falha na autenticação: {he.detail}", exc_info=True)
        raise he
    except Exception as e:
        logger.error(f"Erro na autenticação: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais"
        )

@router.get("/usuarios/me", response_model=schemas.UserResponse)
def obter_info_usuario_atual(usuario_atual: models.User = Depends(obter_usuario_atual)):
    action_logger = get_logger("obter_perfil", usuario_atual)
    try:
        action_logger.info("Solicitação de informações do usuário")
        
        token_acesso = security.create_access_token(data={"sub": usuario_atual.username})
        
        return {
            "id": usuario_atual.id,
            "username": usuario_atual.username,
            "email": usuario_atual.email,
            "access_token": token_acesso,
            "token_type": "bearer"
        }
    except Exception as e:
        action_logger.error(f"Erro ao obter perfil: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao recuperar informações do usuário"
        )

@router.get("/usuarios/{id_usuario}", response_model=schemas.UserResponse)
def obter_usuario_por_id(
    id_usuario: int, 
    db: Session = Depends(get_db), 
    usuario_atual: models.User = Depends(obter_usuario_atual)
):
    action_logger = get_logger("buscar_usuario", usuario_atual, id_usuario)
    try:
        action_logger.info("Iniciando busca por usuário")
        
        try:
            usuario = db.query(models.User).filter(models.User.id == id_usuario).first()
        except Exception as e:
            handle_db_exception(action_logger, e, "busca de usuário")

        if not usuario:
            action_logger.warning("Usuário não encontrado")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        token_acesso = security.create_access_token(data={"sub": usuario.username})
        
        action_logger.info("Busca realizada com sucesso")
        return {
        "id": novo_usuario.id,
        "nome_usuario": novo_usuario.username,
        "email": novo_usuario.email,
        "token_acesso": token_acesso,
        "tipo_token": "bearer"
    }

    except HTTPException as he:
        raise he
    except Exception as e:
        action_logger.error(f"Erro na busca: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar usuário"
        )

@router.put("/usuarios/{id_usuario}", response_model=schemas.UserResponse)
def atualizar_usuario(
    id_usuario: int, 
    usuario_atualizacao: schemas.UserUpdate, 
    db: Session = Depends(get_db), 
    usuario_atual: models.User = Depends(obter_usuario_atual)
):
    action_logger = get_logger("atualizar_usuario", usuario_atual, id_usuario)
    try:
        if usuario_atual.id != id_usuario:
            action_logger.warning("Tentativa de atualizar outro usuário")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso não autorizado"
            )

        try:
            db_usuario = db.query(models.User).filter(models.User.id == id_usuario).first()
        except Exception as e:
            handle_db_exception(action_logger, e, "busca para atualização")

        if not db_usuario:
            action_logger.warning("Usuário não encontrado para atualização")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Validações de atualização
        if usuario_atualizacao.username and usuario_atualizacao.username != db_usuario.username:
            if db.query(models.User).filter(models.User.username == usuario_atualizacao.username).first():
                action_logger.warning("Nome de usuário já existe")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nome de usuário já em uso"
                )

        if usuario_atualizacao.email and usuario_atualizacao.email != db_usuario.email:
            if db.query(models.User).filter(models.User.email == usuario_atualizacao.email).first():
                action_logger.warning("Email já registrado")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email já em uso"
                )

        try:
            # Atualização dos campos
            update_data = usuario_atualizacao.dict(exclude_unset=True)
            for key, value in update_data.items():
                if key == 'password':
                    value = security.get_password_hash(value)
                setattr(db_usuario, key, value)
            
            db.commit()
            db.refresh(db_usuario)
        except Exception as e:
            handle_db_exception(action_logger, e, "atualização de usuário")

        token_acesso = security.create_access_token(data={"sub": db_usuario.username})
        
        action_logger.info("Atualização realizada com sucesso")
        return{
        "id": novo_usuario.id,
        "nome_usuario": novo_usuario.username,
        "email": novo_usuario.email,
        "token_acesso": token_acesso,
        "tipo_token": "bearer"
    }


    except HTTPException as he:
        raise he
    except Exception as e:
        action_logger.error(f"Erro na atualização: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar usuário"
        )

@router.delete("/usuarios/{id_usuario}", status_code=status.HTTP_200_OK)
def excluir_usuario(
    id_usuario: int, 
    db: Session = Depends(get_db), 
    usuario_atual: models.User = Depends(obter_usuario_atual)
):
    action_logger = get_logger("excluir_usuario", usuario_atual, id_usuario)
    try:
        if usuario_atual.id != id_usuario:
            action_logger.warning("Tentativa de excluir outro usuário")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso não autorizado"
            )

        try:
            usuario = db.query(models.User).filter(models.User.id == id_usuario).first()
        except Exception as e:
            handle_db_exception(action_logger, e, "busca para exclusão")

        if not usuario:
            action_logger.warning("Usuário não encontrado para exclusão")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        try:
            db.delete(usuario)
            db.commit()
        except Exception as e:
            handle_db_exception(action_logger, e, "exclusão de usuário")

        action_logger.info("Usuário excluído com sucesso")
        return {"detail": "Conta excluída com sucesso"}

    except HTTPException as he:
        raise he
    except Exception as e:
        action_logger.error(f"Erro na exclusão: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao excluir usuário"
        )


@router.get("/yasmim")
async def yasmim():
    return {"message": "Yasmim LORINHA!!!:)"}