import logging
import sys
from app.core.config import get_settings

settings = get_settings()

import os

def setup_logging():
    """
    Configure structured logging for the application.
    """
    # Ensure LOGS directory exists
    log_dir = os.path.join(os.getcwd(), "LOGS")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler (Main App Log)
    file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
    file_handler.setFormatter(formatter)
    
    # Avoid adding duplicate handlers
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return logger

def get_ocr_logger():
    """Returns a logger specifically for OCR outputs"""
    logger = logging.getLogger("ocr_debugger")
    logger.setLevel(logging.INFO)
    logger.propagate = False # Don't send massive text to root logger
    
    if not logger.handlers:
        log_dir = os.path.join(os.getcwd(), "LOGS")
        os.makedirs(log_dir, exist_ok=True)
        
        handler = logging.FileHandler(os.path.join(log_dir, "ocr_debug.log"), encoding='utf-8')
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logger.addHandler(handler)
    
    return logger
