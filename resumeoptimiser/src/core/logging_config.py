"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from src.core.config import DEBUG, BASE_DIR


def setup_logging():
    """Configure logging for the application."""
    # Create logs directory
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # API handler
    api_handler = RotatingFileHandler(
        logs_dir / "api.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(file_formatter)
    api_logger = logging.getLogger("api")
    api_logger.addHandler(api_handler)
    
    # LLM handler
    llm_handler = RotatingFileHandler(
        logs_dir / "llm.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    llm_handler.setLevel(logging.DEBUG)
    llm_handler.setFormatter(file_formatter)
    llm_logger = logging.getLogger("llm")
    llm_logger.addHandler(llm_handler)
    
    # Generation handler
    gen_handler = RotatingFileHandler(
        logs_dir / "generation.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    gen_handler.setLevel(logging.DEBUG)
    gen_handler.setFormatter(file_formatter)
    gen_logger = logging.getLogger("generation")
    gen_logger.addHandler(gen_handler)
    
    return logger


# Configure on import
logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
