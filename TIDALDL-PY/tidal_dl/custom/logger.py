import logging
from enum import Enum
from logging.handlers import RotatingFileHandler, SMTPHandler
from typing import Optional, Dict, Any
from colorama import init, Fore, Style
import os
import time
import shutil

# Initialize colorama
init(autoreset=True)

class SafeRotatingFileHandler(RotatingFileHandler):
    """A rotating file handler that handles file locks better on Windows."""
    
    def __init__(self, *args, max_retries: int = 5, retry_delay: float = 0.1, **kwargs) -> None:
        """
        Initialize the handler with retry parameters.

        Args:
            *args: Arguments for RotatingFileHandler
            max_retries: Maximum number of retry attempts for file operations
            retry_delay: Delay between retry attempts in seconds
            **kwargs: Keyword arguments for RotatingFileHandler
        """
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _handle_file_operation(self, operation: callable, error_msg: str) -> bool:
        """
        Handle file operations with retries.

        Args:
            operation: Callable that performs the file operation
            error_msg: Error message to log if all retries fail

        Returns:
            bool: True if operation succeeded, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                operation()
                return True
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"{error_msg}: {str(e)}")
                    return False
                time.sleep(self.retry_delay)
        return False

    def doRollover(self) -> None:
        """
        Do a rollover, as described in __init__().
        Handles file operations with retries and proper error handling.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0:
            # Close the file
            if self.stream:
                self.stream.close()
                self.stream = None

            # Remove oldest backup
            def remove_oldest():
                if os.path.exists(f"{self.baseFilename}.{self.backupCount}"):
                    os.remove(f"{self.baseFilename}.{self.backupCount}")
            
            self._handle_file_operation(
                remove_oldest,
                f"Failed to remove oldest backup file {self.baseFilename}.{self.backupCount}"
            )

            # Rotate existing backups
            for i in range(self.backupCount - 1, 0, -1):
                sfn = f"{self.baseFilename}.{i}"
                dfn = f"{self.baseFilename}.{i + 1}"

                def rotate_backup(src=sfn, dst=dfn):
                    if os.path.exists(src):
                        if os.path.exists(dst):
                            os.remove(dst)
                        shutil.move(src, dst)

                self._handle_file_operation(
                    lambda: rotate_backup(sfn, dfn),
                    f"Failed to rotate backup file {sfn} to {dfn}"
                )

            # Rotate current file
            def rotate_current():
                dfn = f"{self.baseFilename}.1"
                if os.path.exists(dfn):
                    os.remove(dfn)
                if os.path.exists(self.baseFilename):
                    shutil.move(self.baseFilename, dfn)

            self._handle_file_operation(
                rotate_current,
                f"Failed to rotate current file {self.baseFilename}"
            )

        if not self.delay:
            self.stream = self._open()

class LogLevel(Enum):
    """Enum for logging levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class ColorFormatter(logging.Formatter):
    """Custom formatter to add colors to console output."""
    
    COLORS: Dict[LogLevel, str] = {
        LogLevel.DEBUG: Fore.BLUE,
        LogLevel.INFO: Fore.GREEN,
        LogLevel.WARNING: Fore.YELLOW,
        LogLevel.ERROR: Fore.RED,
        LogLevel.CRITICAL: Fore.MAGENTA
    }

    def __init__(self, *args, **kwargs) -> None:
        """Initialize formatter with color support."""
        super().__init__(*args, **kwargs)
        self._default_color = Style.RESET_ALL

    def _get_color(self, level: int) -> str:
        """
        Get the color for a given log level.
        
        Args:
            level: Logging level number
            
        Returns:
            ANSI color code string
        """
        try:
            return self.COLORS.get(LogLevel(level), self._default_color)
        except ValueError:
            return self._default_color

    def _colorize(self, text: str, color: str) -> str:
        """
        Add color to text.
        
        Args:
            text: Text to colorize
            color: ANSI color code
            
        Returns:
            Colorized text
        """
        return f"{color}{text}{self._default_color}" if color else text

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with colors.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log message with colors
        """
        try:
            log_message = super().format(record)
            color = self._get_color(record.levelno)
            
            # Format each component with color
            components = {
                'asctime': getattr(record, 'asctime', ''),
                'name': record.name,
                'levelname': record.levelname
            }
            
            for key, value in components.items():
                if value and value in log_message:
                    colored_value = self._colorize(value, color)
                    log_message = log_message.replace(value, colored_value)
                    
            return log_message
        except Exception as e:
            # Log the error and fallback to basic formatting
            logging.error(f"Color formatting failed: {str(e)}")
            return super().format(record)

class Logger:
    """Main logger class that wraps the standard Python logger with additional functionality."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize Logger with a configured logging.Logger instance.
        
        Args:
            logger: Configured logging.Logger instance
        """
        self._logger = logger

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.critical(msg, *args, **kwargs)

    def close_handlers(self) -> None:
        """Safely close and remove all handlers."""
        for handler in self._logger.handlers[:]:  # Create a copy of the list
            try:
                handler.acquire()
                handler.close()
                self._logger.removeHandler(handler)
            except Exception:
                pass  # Ensure we continue closing other handlers
            finally:
                handler.release()

class LoggerConfig:
    """Configuration class for creating logger instances with multiple outputs."""
    
    # Configuration constants
    REQUIRED_EMAIL_FIELDS = {'mailhost', 'port', 'fromaddr', 'toaddrs', 'subject', 'username', 'password'}
    MIN_FILE_SIZE = 1024 * 1024  # 1MB
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MIN_BACKUP_COUNT = 1
    MAX_BACKUP_COUNT = 10

    @staticmethod
    def _validate_file_size(size: int) -> None:
        """
        Validate file size is within acceptable range.
        
        Args:
            size: Size in bytes
            
        Raises:
            ValueError: If size is invalid
        """
        if not isinstance(size, int) or size < LoggerConfig.MIN_FILE_SIZE or size > LoggerConfig.MAX_FILE_SIZE:
            raise ValueError(
                f"File size must be between {LoggerConfig.MIN_FILE_SIZE} and {LoggerConfig.MAX_FILE_SIZE} bytes"
            )

    @staticmethod
    def _validate_backup_count(count: int) -> None:
        """
        Validate backup count is within acceptable range.
        
        Args:
            count: Number of backups
            
        Raises:
            ValueError: If count is invalid
        """
        if not isinstance(count, int) or count < LoggerConfig.MIN_BACKUP_COUNT or count > LoggerConfig.MAX_BACKUP_COUNT:
            raise ValueError(
                f"Backup count must be between {LoggerConfig.MIN_BACKUP_COUNT} and {LoggerConfig.MAX_BACKUP_COUNT}"
            )

    @staticmethod
    def _validate_email_config(config: Dict[str, Any]) -> None:
        """
        Validate email configuration has all required fields.
        
        Args:
            config: Email configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not config:
            return

        missing_fields = LoggerConfig.REQUIRED_EMAIL_FIELDS - set(config.keys())
        if missing_fields:
            raise ValueError(f"Missing required email configuration fields: {missing_fields}")

        if not isinstance(config['port'], int) or not 0 < config['port'] < 65536:
            raise ValueError("Email port must be a valid port number (1-65535)")

        if not isinstance(config['toaddrs'], (list, tuple)) or not config['toaddrs']:
            raise ValueError("Email toaddrs must be a non-empty list of addresses")

        for field in ['fromaddr', 'subject', 'username', 'password']:
            if not isinstance(config[field], str) or not config[field].strip():
                raise ValueError(f"Email {field} must be a non-empty string")

    def update_config(
        self,
        level: Optional[LogLevel] = None,
        log_file: Optional[str] = None,
        email_config: Optional[Dict[str, Any]] = None,
        max_file_size: Optional[int] = None,
        backup_count: Optional[int] = None
    ) -> None:
        """
        Update logger configuration parameters.
        
        Args:
            level: New logging level
            log_file: New log file path
            email_config: New email configuration
            max_file_size: New maximum file size
            backup_count: New backup count
            
        Raises:
            ValueError: If any parameters are invalid
        """
        if level is not None and not isinstance(level, LogLevel):
            raise ValueError("Level must be a LogLevel enum value")

        if max_file_size is not None:
            self._validate_file_size(max_file_size)

        if backup_count is not None:
            self._validate_backup_count(backup_count)

        if email_config is not None:
            self._validate_email_config(email_config)

        # Update values if provided
        if level is not None:
            self.level = level
        if log_file is not None:
            self.log_file = log_file.strip()
        if email_config is not None:
            self.email_config = email_config
        if max_file_size is not None:
            self.max_file_size = max_file_size
        if backup_count is not None:
            self.backup_count = backup_count

        # If logger exists, update its configuration
        if hasattr(self, '_logger') and self._logger:
            self._logger.close_handlers()
            self._logger = self.create()

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        log_file: Optional[str] = None,
        email_config: Optional[Dict[str, Any]] = None,
        max_file_size: int = 5 * 1024 * 1024,  # 5MB default
        backup_count: int = 3
    ):
        """
        Initialize LoggerConfig with specified parameters.
        
        Args:
            name: Name of the logger
            level: Logging level from LogLevel enum
            log_file: Optional path to log file
            email_config: Optional email configuration for email handler
            max_file_size: Maximum size of log file before rotation in bytes
            backup_count: Number of backup files to keep
            
        Raises:
            ValueError: If any parameters are invalid
        """
        if not name or not name.strip():
            raise ValueError("Logger name cannot be empty")

        if not isinstance(level, LogLevel):
            raise ValueError("Level must be a LogLevel enum value")

        self._validate_file_size(max_file_size)
        self._validate_backup_count(backup_count)
        if email_config:
            self._validate_email_config(email_config)

        self.name = name.strip()
        self.level = level
        self.log_file = log_file.strip() if log_file else None
        self.email_config = email_config
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self._logger: Optional[Logger] = None

    def create(self) -> Logger:
        """
        Create and configure a new Logger instance.
        
        Returns:
            Configured Logger instance
        """
        logger = logging.Logger(self.name)
        logger.setLevel(self.level.value)

        # Create formatters
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        color_formatter = ColorFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Add console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level.value)
        console_handler.setFormatter(color_formatter)
        logger.addHandler(console_handler)

        # Add file handler if specified
        if self.log_file:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
                
                file_handler = SafeRotatingFileHandler(
                    self.log_file,
                    maxBytes=self.max_file_size,
                    backupCount=self.backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(self.level.value)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                console_handler.emit(
                    logging.LogRecord(
                        self.name, logging.ERROR, "", 0,
                        f"Failed to initialize file handler: {str(e)}", (), None
                    )
                )

        # Add email handler if configured
        if self.email_config:
            try:
                email_handler = SMTPHandler(
                    mailhost=(self.email_config["mailhost"], self.email_config["port"]),
                    fromaddr=self.email_config["fromaddr"],
                    toaddrs=self.email_config["toaddrs"],
                    subject=self.email_config["subject"],
                    credentials=(self.email_config["username"], self.email_config["password"]),
                    secure=self.email_config.get("secure", None)
                )
                email_handler.setLevel(LogLevel.ERROR.value)  # Email only errors and critical
                email_handler.setFormatter(formatter)
                logger.addHandler(email_handler)
            except Exception as e:
                console_handler.emit(
                    logging.LogRecord(
                        self.name, logging.ERROR, "", 0,
                        f"Failed to initialize email handler: {str(e)}", (), None
                    )
                )

        return Logger(logger)