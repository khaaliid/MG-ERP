import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
try:
    from .config import auth_settings
except ImportError:
    from config import auth_settings

def setup_logging():
    """Setup logging configuration"""
    
    log_to_stdout = os.getenv("LOG_TO_STDOUT", "true").lower() == "true"

    # If not pure stdout, prepare file log directory
    if not log_to_stdout:
        configured_log_dir = os.getenv("LOG_DIR", "logs")
        log_dir = Path(configured_log_dir)
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback = Path("/tmp/auth-logs")
            fallback.mkdir(parents=True, exist_ok=True)
            log_dir = fallback
            print(f"[LOGGING] Permission denied for {configured_log_dir}, using {log_dir}")
    else:
        log_dir = None
    
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
    
    if not log_to_stdout:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        # File handler for general logs
        file_handler = RotatingFileHandler(
            log_dir / "auth_service.log",
            maxBytes=10_000_000,
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Error file handler
        error_handler = RotatingFileHandler(
            log_dir / "auth_errors.log",
            maxBytes=10_000_000,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

        # Audit logger
        audit_handler = RotatingFileHandler(
            log_dir / "auth_audit.log",
            maxBytes=10_000_000,
            backupCount=10
        )
        audit_handler.setLevel(logging.INFO)
        audit_formatter = logging.Formatter('%(asctime)s - AUDIT - %(message)s')
        audit_handler.setFormatter(audit_formatter)
        audit_logger = logging.getLogger('auth.audit')
        audit_logger.setLevel(logging.INFO)
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False
    else:
        # Provide audit logger that writes to stdout only
        audit_logger = logging.getLogger('auth.audit')
        audit_logger.setLevel(logging.INFO)
        if not any(isinstance(h, logging.StreamHandler) for h in audit_logger.handlers):
            audit_logger.addHandler(console_handler)
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