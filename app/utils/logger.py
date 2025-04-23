import logging
import sys
from loguru import logger as loguru_logger
from config import settings

# Remove default loguru handler
loguru_logger.remove()

# Configure loguru logger
def setup_logging():
    """Set up structured logging with loguru"""
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    # Set logging level from config
    log_level = settings.LOG_LEVEL.upper()
    
    # Add console handler
    loguru_logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler for errors and above
    loguru_logger.add(
        "logs/error.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="1 week",
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler for all logs
    loguru_logger.add(
        "logs/app.log",
        format=log_format,
        level=log_level,
        rotation="10 MB",
        retention="1 week",
    )
    
    # Intercept standard library logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding loguru level
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
    
    # Configure standard library logging to use loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    logger.info("Logging configured successfully")

# Export logger
logger = loguru_logger

# Add context information to logs
def add_request_id(request_id: str):
    """Add request ID to logger context"""
    logger.configure(extra={"request_id": request_id})

# Example usage: logger.bind(user_id="123").info("User logged in")
