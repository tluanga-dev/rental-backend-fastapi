"""
Centralized Logging Configuration

This module provides centralized configuration for all logging components
including transaction logging, audit logging, and API request/response logging.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class LoggingConfig:
    """Configuration class for all logging settings."""
    
    # General logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File logging settings
    log_directory: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # Transaction logging settings
    transaction_log_directory: str = "logs/transactions"
    transaction_log_enabled: bool = True
    
    # API logging settings
    api_log_enabled: bool = True
    api_log_include_request_body: bool = True
    api_log_include_response_body: bool = False
    api_log_max_body_size: int = 10000
    
    # Audit logging settings
    audit_log_enabled: bool = True
    
    # Performance logging settings
    slow_query_threshold: float = 1.0  # seconds
    log_sql_queries: bool = False
    
    # Error tracking settings
    error_tracking_enabled: bool = True
    capture_stack_traces: bool = True


class LoggingManager:
    """
    Centralized logging manager for the entire application.
    
    This class manages all logging configurations including:
    - Standard application logging
    - Transaction logging
    - API request/response logging
    - Audit logging
    - Error tracking
    """
    
    def __init__(self, config: Optional[LoggingConfig] = None):
        """
        Initialize the logging manager.
        
        Args:
            config: Logging configuration. If None, uses default configuration.
        """
        self.config = config or LoggingConfig()
        self._setup_directories()
        self._configure_root_logger()
        self._loggers: Dict[str, logging.Logger] = {}
        
    def _setup_directories(self) -> None:
        """Create necessary log directories."""
        directories = [
            self.config.log_directory,
            self.config.transaction_log_directory,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
    def _configure_root_logger(self) -> None:
        """Configure the root logger with basic settings."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format=self.config.log_format,
            handlers=[
                logging.StreamHandler(),  # Console output
                self._create_file_handler("app.log")  # File output
            ]
        )
        
    def _create_file_handler(self, filename: str, log_dir: Optional[str] = None) -> logging.Handler:
        """
        Create a rotating file handler.
        
        Args:
            filename: Name of the log file
            log_dir: Directory for the log file. Uses default if None.
            
        Returns:
            Configured file handler
        """
        log_dir = log_dir or self.config.log_directory
        log_path = Path(log_dir) / filename
        
        handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count
        )
        
        formatter = logging.Formatter(self.config.log_format)
        handler.setFormatter(formatter)
        
        return handler
        
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the given name.
        
        Args:
            name: Logger name
            
        Returns:
            Configured logger instance
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(getattr(logging, self.config.log_level.upper()))
            
            # Add file handler specific to this logger
            if name not in ["root", ""]:
                file_handler = self._create_file_handler(f"{name}.log")
                logger.addHandler(file_handler)
                
            self._loggers[name] = logger
            
        return self._loggers[name]
        
    def get_transaction_logger(self) -> logging.Logger:
        """Get logger specifically for transaction operations."""
        return self.get_logger("transaction")
        
    def get_api_logger(self) -> logging.Logger:
        """Get logger specifically for API operations."""
        return self.get_logger("api")
        
    def get_audit_logger(self) -> logging.Logger:
        """Get logger specifically for audit operations."""
        return self.get_logger("audit")
        
    def get_error_logger(self) -> logging.Logger:
        """Get logger specifically for error tracking."""
        return self.get_logger("error")
        
    def get_performance_logger(self) -> logging.Logger:
        """Get logger specifically for performance monitoring."""
        return self.get_logger("performance")
        
    def configure_transaction_logging(self) -> None:
        """Configure transaction-specific logging settings."""
        if not self.config.transaction_log_enabled:
            return
            
        transaction_logger = self.get_transaction_logger()
        
        # Add transaction-specific handler
        handler = self._create_file_handler(
            "transactions.log", 
            self.config.transaction_log_directory
        )
        transaction_logger.addHandler(handler)
        
        # Configure transaction logger to not propagate to root logger
        # to avoid duplicate log entries
        transaction_logger.propagate = False
        
    def configure_api_logging(self) -> None:
        """Configure API request/response logging settings."""
        if not self.config.api_log_enabled:
            return
            
        api_logger = self.get_api_logger()
        
        # Add API-specific handler
        handler = self._create_file_handler("api.log")
        api_logger.addHandler(handler)
        
    def configure_audit_logging(self) -> None:
        """Configure audit logging settings."""
        if not self.config.audit_log_enabled:
            return
            
        audit_logger = self.get_audit_logger()
        
        # Add audit-specific handler
        handler = self._create_file_handler("audit.log")
        audit_logger.addHandler(handler)
        
    def configure_error_tracking(self) -> None:
        """Configure error tracking and logging."""
        if not self.config.error_tracking_enabled:
            return
            
        error_logger = self.get_error_logger()
        
        # Add error-specific handler
        handler = self._create_file_handler("errors.log")
        error_logger.addHandler(handler)
        
        # Set error logger to WARNING level to capture warnings and errors
        error_logger.setLevel(logging.WARNING)
        
    def configure_performance_logging(self) -> None:
        """Configure performance monitoring and logging."""
        performance_logger = self.get_performance_logger()
        
        # Add performance-specific handler
        handler = self._create_file_handler("performance.log")
        performance_logger.addHandler(handler)
        
    def setup_all_logging(self) -> None:
        """Set up all logging configurations."""
        self.configure_transaction_logging()
        self.configure_api_logging()
        self.configure_audit_logging()
        self.configure_error_tracking()
        self.configure_performance_logging()
        
    def log_application_startup(self) -> None:
        """Log application startup information."""
        logger = self.get_logger("startup")
        logger.info("=== Application Starting ===")
        logger.info(f"Log Level: {self.config.log_level}")
        logger.info(f"Log Directory: {self.config.log_directory}")
        logger.info(f"Transaction Logging: {'Enabled' if self.config.transaction_log_enabled else 'Disabled'}")
        logger.info(f"API Logging: {'Enabled' if self.config.api_log_enabled else 'Disabled'}")
        logger.info(f"Audit Logging: {'Enabled' if self.config.audit_log_enabled else 'Disabled'}")
        logger.info("=== Logging Configuration Complete ===")
        
    def get_logging_status(self) -> Dict[str, Any]:
        """
        Get current logging status and configuration.
        
        Returns:
            Dictionary containing logging status information
        """
        return {
            "config": {
                "log_level": self.config.log_level,
                "log_directory": self.config.log_directory,
                "transaction_log_directory": self.config.transaction_log_directory,
                "transaction_logging_enabled": self.config.transaction_log_enabled,
                "api_logging_enabled": self.config.api_log_enabled,
                "audit_logging_enabled": self.config.audit_log_enabled,
                "error_tracking_enabled": self.config.error_tracking_enabled,
            },
            "loggers": list(self._loggers.keys()),
            "log_files": {
                "app": f"{self.config.log_directory}/app.log",
                "transaction": f"{self.config.transaction_log_directory}/transactions.log",
                "api": f"{self.config.log_directory}/api.log",
                "audit": f"{self.config.log_directory}/audit.log",
                "error": f"{self.config.log_directory}/errors.log",
                "performance": f"{self.config.log_directory}/performance.log",
            }
        }


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def get_logging_manager() -> LoggingManager:
    """
    Get the global logging manager instance.
    
    Returns:
        Global LoggingManager instance
    """
    global _logging_manager
    if _logging_manager is None:
        # Create configuration from environment or use defaults
        config = LoggingConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_directory=os.getenv("LOG_DIRECTORY", "logs"),
            transaction_log_directory=os.getenv("TRANSACTION_LOG_DIRECTORY", "logs/transactions"),
            transaction_log_enabled=os.getenv("TRANSACTION_LOG_ENABLED", "true").lower() == "true",
            api_log_enabled=os.getenv("API_LOG_ENABLED", "true").lower() == "true",
            audit_log_enabled=os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true",
            error_tracking_enabled=os.getenv("ERROR_TRACKING_ENABLED", "true").lower() == "true",
        )
        
        _logging_manager = LoggingManager(config)
        _logging_manager.setup_all_logging()
        
    return _logging_manager


def setup_application_logging() -> None:
    """Initialize application logging on startup."""
    manager = get_logging_manager()
    manager.log_application_startup()


# Convenience functions for getting specific loggers
def get_transaction_logger() -> logging.Logger:
    """Get transaction logger."""
    return get_logging_manager().get_transaction_logger()


def get_api_logger() -> logging.Logger:
    """Get API logger."""
    return get_logging_manager().get_api_logger()


def get_audit_logger() -> logging.Logger:
    """Get audit logger."""
    return get_logging_manager().get_audit_logger()


def get_error_logger() -> logging.Logger:
    """Get error logger."""
    return get_logging_manager().get_error_logger()


def get_performance_logger() -> logging.Logger:
    """Get performance logger."""
    return get_logging_manager().get_performance_logger()


def get_application_logger(name: str) -> logging.Logger:
    """
    Get application logger by name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return get_logging_manager().get_logger(name)