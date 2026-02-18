"""
Centralized logging configuration for the application.
Provides structured logging with file rotation, error tracking, and performance monitoring.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
from datetime import datetime
import traceback
import functools
import time


class AppLogger:
    """Centralized application logger with multiple handlers."""

    def __init__(self, name: str = "family_health_manager"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Setup console and file handlers with formatters."""

        # Create logs directory - use /app/logs in Docker, relative otherwise
        import os
        if os.path.exists("/app"):
            log_dir = Path("/app/logs")
        else:
            log_dir = Path(__file__).resolve().parents[2] / "logs"
        log_dir.mkdir(exist_ok=True)

        # Console Handler - INFO and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # File Handler - DEBUG and above (rotating by size)
        debug_log = log_dir / "debug.log"
        debug_handler = RotatingFileHandler(
            debug_log,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        debug_handler.setFormatter(debug_formatter)

        # Error Handler - ERROR and above (rotating daily)
        error_log = log_dir / "error.log"
        error_handler = TimedRotatingFileHandler(
            error_log,
            when='midnight',
            interval=1,
            backupCount=30  # Keep 30 days
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d\n'
            'Message: %(message)s\n'
            '%(exc_info)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)

        # Database Handler - Separate log for database operations
        db_log = log_dir / "database.log"
        db_handler = RotatingFileHandler(
            db_log,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        db_handler.setLevel(logging.DEBUG)
        db_handler.setFormatter(debug_formatter)
        # Filter to only database-related logs
        db_handler.addFilter(lambda record: 'database' in record.name.lower() or 'postgres' in record.name.lower() or 'redis' in record.name.lower() or 'neo4j' in record.name.lower())

        # Performance Handler - Track slow operations
        perf_log = log_dir / "performance.log"
        perf_handler = RotatingFileHandler(
            perf_log,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(debug_formatter)
        perf_handler.addFilter(lambda record: 'performance' in record.getMessage().lower() or 'slow' in record.getMessage().lower())

        # Add all handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(db_handler)
        self.logger.addHandler(perf_handler)

    def get_logger(self, module_name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance for a specific module.

        Args:
            module_name: Optional module name (e.g., 'postgres', 'redis', 'neo4j')

        Returns:
            Logger instance
        """
        if module_name:
            return logging.getLogger(f"{self.name}.{module_name}")
        return self.logger

    def log_exception(self, exc: Exception, context: Optional[dict] = None, logger: Optional[logging.Logger] = None):
        """
        Log exception with full stack trace and context.

        Args:
            exc: Exception instance
            context: Optional context dictionary
            logger: Optional logger instance (uses root logger if None)
        """
        log = logger or self.logger

        error_msg = f"Exception occurred: {type(exc).__name__}: {str(exc)}"
        if context:
            error_msg += f"\nContext: {context}"

        log.error(error_msg, exc_info=True)

    def log_performance(self, operation: str, duration: float, threshold: float = 1.0, logger: Optional[logging.Logger] = None):
        """
        Log performance metrics for operations.

        Args:
            operation: Operation name
            duration: Duration in seconds
            threshold: Threshold in seconds (log warning if exceeded)
            logger: Optional logger instance
        """
        log = logger or self.logger

        if duration > threshold:
            log.warning(f"PERFORMANCE: Slow operation '{operation}' took {duration:.3f}s (threshold: {threshold}s)")
        else:
            log.info(f"PERFORMANCE: Operation '{operation}' completed in {duration:.3f}s")


# Global logger instance
app_logger = AppLogger()


def get_logger(module_name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a module.

    Usage:
        logger = get_logger('postgres')
        logger.info("Database connected")

    Args:
        module_name: Module name (e.g., 'postgres', 'redis', 'neo4j')

    Returns:
        Logger instance
    """
    return app_logger.get_logger(module_name)


def log_function_call(logger: Optional[logging.Logger] = None, log_args: bool = False):
    """
    Decorator to log function calls with timing.

    Usage:
        @log_function_call(logger=get_logger('postgres'), log_args=True)
        def create_user(user_id: str):
            ...

    Args:
        logger: Logger instance
        log_args: Whether to log function arguments
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            func_name = func.__name__

            # Log function entry
            if log_args:
                log.debug(f"Calling {func_name} with args={args}, kwargs={kwargs}")
            else:
                log.debug(f"Calling {func_name}")

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log success
                log.debug(f"{func_name} completed successfully in {duration:.3f}s")

                # Log performance warning if slow
                if duration > 1.0:
                    log.warning(f"PERFORMANCE: {func_name} took {duration:.3f}s")

                return result

            except Exception as e:
                duration = time.time() - start_time
                log.error(f"{func_name} failed after {duration:.3f}s: {type(e).__name__}: {str(e)}", exc_info=True)
                raise

        return wrapper
    return decorator


def log_database_operation(operation_type: str, logger: Optional[logging.Logger] = None):
    """
    Decorator to log database operations with performance tracking.

    Usage:
        @log_database_operation('CREATE', logger=get_logger('postgres'))
        def create_conversation(self, conversation_id: str):
            ...

    Args:
        operation_type: Type of operation (CREATE, READ, UPDATE, DELETE, QUERY)
        logger: Logger instance
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            func_name = func.__name__

            log.debug(f"DB {operation_type}: {func_name} started")
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log success with timing
                log.info(f"DB {operation_type}: {func_name} completed in {duration:.3f}s")

                # Log performance warning for slow queries
                if duration > 2.0:
                    log.warning(f"PERFORMANCE: Slow DB {operation_type} in {func_name} took {duration:.3f}s")

                return result

            except Exception as e:
                duration = time.time() - start_time
                log.error(
                    f"DB {operation_type}: {func_name} failed after {duration:.3f}s - "
                    f"{type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                raise

        return wrapper
    return decorator
