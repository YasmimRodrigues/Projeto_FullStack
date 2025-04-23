from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import auth_controller, user_controller
from app.database.session import init_db
from app.utils.logger import logger
from config import settings

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    # Initialize FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        description="A FastAPI login system with MVC architecture",
        version="1.0.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify the allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize database
    init_db()
    
    # Include routers
    app.include_router(
        auth_controller.router,
        prefix=f"{settings.API_PREFIX}/auth",
        tags=["Authentication"],
    )
    app.include_router(
        user_controller.router,
        prefix=f"{settings.API_PREFIX}/users",
        tags=["Users"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "Welcome to the FastAPI Login System"}
    
    @app.on_event("startup")
    async def startup():
        logger.info("Application starting up")
    
    @app.on_event("shutdown")
    async def shutdown():
        logger.info("Application shutting down")
    
    return app
