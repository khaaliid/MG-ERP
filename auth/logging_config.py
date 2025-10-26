import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
try:
    from .config import auth_settings
except ImportError:
    from config import auth_settings

def setup_logging():
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if auth_settings.DEBUG else logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if auth_settings.DEBUG else logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for general logs
    file_handler = RotatingFileHandler(
        log_dir / "auth_service.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = RotatingFileHandler(
        log_dir / "auth_errors.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Security audit handler
    audit_handler = RotatingFileHandler(
        log_dir / "auth_audit.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=10
    )
    audit_handler.setLevel(logging.INFO)
    audit_formatter = logging.Formatter(
        '%(asctime)s - AUDIT - %(message)s'
    )
    audit_handler.setFormatter(audit_formatter)
    
    # Create audit logger
    audit_logger = logging.getLogger('auth.audit')
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(audit_handler)
    audit_logger.propagate = False
    
    # Set library log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if not auth_settings.DEBUG else logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if not auth_settings.DEBUG else logging.INFO)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

def get_audit_logger():
    """Get the audit logger"""
    return logging.getLogger('auth.audit')