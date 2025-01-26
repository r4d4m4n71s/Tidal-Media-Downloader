import logging
from enum import Enum
from logging.handlers import RotatingFileHandler, SMTPHandler
from urllib.request import FTPHandler
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class LogLevel(Enum):
    """ Enum for logging levels. """
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class ColorFormatter(logging.Formatter):
    """ Custom formatter to add colors to console output. """
    COLORS = {
        LogLevel.DEBUG: Fore.BLUE,
        LogLevel.INFO: Fore.GREEN,
        LogLevel.WARNING: Fore.YELLOW,
        LogLevel.ERROR: Fore.RED,
        LogLevel.CRITICAL: Fore.MAGENTA
    }

    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(LogLevel(record.levelno), "")
        asctime = f"{color}{record.asctime}{Style.RESET_ALL}"
        name = f"{color}{record.name}{Style.RESET_ALL}"
        levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        log_message = log_message.replace(record.asctime, asctime).replace(record.name, name).replace(record.levelname, levelname)
        return log_message

class LoggerConfig:
    """
    A class to configure and manage logger instances with multiple outputs (Console, File, FTP, Email).
    """

    def __init__(self, name: str = "app_logger", log_file: str = None, level: LogLevel = LogLevel.DEBUG,
                 email_config: dict = None, ftp_config: dict = None):
        """
        Initialize the LoggerConfig instance.
        
        Args:
            name (str): Name of the logger.
            log_file (str): File to write logs to. If None, no file logging is configured.
            level (LogLevel): Logging level from LogLevel Enum (e.g., LogLevel.DEBUG).
            email_config (dict): Email configuration for email handler (optional).
            ftp_config (dict): FTP configuration for FTP handler (optional).
        """
        self.name = name
        self.log_file = log_file
        self.level = level
        self.email_config = email_config
        self.ftp_config = ftp_config
        self.logger = self._create_logger()

    def _create_logger(self):
        """
        Internal method to create and configure the logger.
        """
        import logging  # Importing logging here, within the class, instead of globally

        # Create a logger instance
        #logger = logging.getLogger(self.name)
        logger = logging.Logger(self.name)
        
        # Set the logging level using the Enum value
        logger.setLevel(self.level.value)

        # Define a formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        color_formatter = ColorFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Console handler (streaming to the console)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level.value)
        console_handler.setFormatter(color_formatter)
        logger.addHandler(console_handler)

        # File handler (if log_file is specified)
        if self.log_file:
            file_handler = RotatingFileHandler(
                self.log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
            )
            file_handler.setLevel(self.level.value)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # FTP handler (if ftp_config is provided)
        if self.ftp_config:
            ftp_handler = FTPHandler(
                self.ftp_config["host"], self.ftp_config["username"], self.ftp_config["password"], 
                self.ftp_config["remote_path"]
            )
            ftp_handler.setLevel(self.level.value)
            ftp_handler.setFormatter(formatter)
            logger.addHandler(ftp_handler)

        # Email handler (if email_config is provided)
        if self.email_config:
            email_handler = SMTPHandler(
                mailhost=(self.email_config["mailhost"], self.email_config["port"]),
                fromaddr=self.email_config["fromaddr"],
                toaddrs=self.email_config["toaddrs"],
                subject=self.email_config["subject"],
                credentials=(self.email_config["username"], self.email_config["password"]),
                secure=self.email_config.get("secure", None)
            )
            email_handler.setLevel(self.level.value)
            email_handler.setFormatter(formatter)
            logger.addHandler(email_handler)

        return logger

    def get_logger(self, name = None):
        """
        Returns the configured logger instance.
        
        Returns:
            logging.Logger: The configured logger.
        """
        if name:
            return logging.getLogger(name)

        return self.logger

    def _close_handlers(self):
        """
        Close all handlers associated with the logger.
        """
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
     
    def _remove_handlers(self):
        handlers = self.logger.handlers[:]
        for handler in handlers:
            self.logger.removeHandler(handler)

# Define logger as a global variable
logger_config = LoggerConfig(name="log", level=LogLevel.DEBUG)
logger = logger_config.get_logger()

