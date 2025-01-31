import os
import sys
import unittest
from io import StringIO
import logging
import time
from typing import Optional
from unittest.mock import patch

# Adjust the path to include the directory containing the logger_config module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tidal_dl')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tidal_dl/custom')))

from tidal_dl.custom.logger import LoggerConfig, LogLevel, Logger, ColorFormatter  # type: ignore

class TestLoggerConfigRegression(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test environment before each test."""
        # Create absolute path for test output
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(self.base_dir, "..", "output")
        self.log_file = os.path.join(self.log_dir, "app.log")
        
        # Ensure output directory exists and is clean
        os.makedirs(self.log_dir, exist_ok=True)
        self.cleanup_log_files()
        
        # Basic logger setup
        self.logger_config = LoggerConfig(
            name="test_logger",
            log_file=self.log_file,
            level=LogLevel.DEBUG
        )
        self.logger = self.logger_config.create()

    def tearDown(self) -> None:
        """Clean up test environment after each test."""
        try:
            # Close handlers first
            if hasattr(self, 'logger'):
                self.logger.close_handlers()
            
            # Clean up files
            self.cleanup_log_files()
        except Exception as e:
            print(f"Error in tearDown: {str(e)}")

    def cleanup_log_files(self) -> None:
        """Helper method to clean up log files."""
        try:
            files_to_remove = [self.log_file] + [f"{self.log_file}.{i}" for i in range(1, 4)]
            for file in files_to_remove:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                    except (PermissionError, OSError):
                        time.sleep(0.1)  # Wait a bit and try again
                        if os.path.exists(file):
                            os.remove(file)
        except Exception as e:
            print(f"Error cleaning up files: {str(e)}")

    def read_log_file(self, filename: Optional[str] = None) -> str:
        """Helper method to read log file contents."""
        try:
            self.logger.close_handlers()  # Ensure handlers are closed
            filepath = filename or self.log_file
            if os.path.exists(filepath):
                with open(filepath, "r", encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            print(f"Error reading log file: {str(e)}")
            return ""

    def test_basic_logging_levels(self) -> None:
        """Test all logging levels write to file correctly."""
        test_messages = {
            "debug": "Debug test message",
            "info": "Info test message",
            "warning": "Warning test message",
            "error": "Error test message",
            "critical": "Critical test message"
        }

        # Write test messages
        for level, message in test_messages.items():
            getattr(self.logger, level)(message)

        # Verify messages in log file
        log_content = self.read_log_file()
        for level, message in test_messages.items():
            self.assertIn(message, log_content, f"Message '{message}' not found in log")
            self.assertIn(level.upper(), log_content, f"Level '{level.upper()}' not found in log")

    def test_console_output_with_colors(self) -> None:
        """Test console output includes color codes."""
        # Capture console output
        console_output = StringIO()
        console_handler = logging.StreamHandler(console_output)
        console_handler.setFormatter(ColorFormatter("%(levelname)s - %(message)s"))
        
        # Create test logger
        test_logger = logging.Logger("color_test")
        test_logger.addHandler(console_handler)
        test_logger.setLevel(LogLevel.DEBUG.value)
        
        # Create wrapped logger
        wrapped_logger = Logger(test_logger)

        # Test messages
        test_message = "Test message"
        wrapped_logger.info(test_message)
        wrapped_logger.error(test_message)

        # Get output and clean up
        output = console_output.getvalue()
        console_output.close()

        # Verify color codes
        self.assertIn("\x1b[32m", output, "Green color code not found")  # Green for INFO
        self.assertIn("\x1b[31m", output, "Red color code not found")    # Red for ERROR
        self.assertIn("\x1b[0m", output, "Reset code not found")         # Reset code
        self.assertIn(test_message, output, "Test message not found in output")

    def test_logger_without_file(self) -> None:
        """Test logger works correctly without file handler."""
        console_logger = LoggerConfig(
            name="console_test",
            level=LogLevel.INFO
        ).create()

        # Should work without errors
        test_message = "Console only message"
        console_logger.info(test_message)
        
        # Verify only console handler exists
        handlers = console_logger._logger.handlers
        self.assertEqual(len(handlers), 1, "Expected exactly one handler")
        self.assertIsInstance(handlers[0], logging.StreamHandler, "Handler is not StreamHandler")

    @patch('tidal_dl.custom.logger.LoggerConfig.MIN_FILE_SIZE', 200)  # 200 bytes
    @patch('tidal_dl.custom.logger.LoggerConfig.MAX_FILE_SIZE', 500)  # 500 bytes
    def test_file_rotation(self) -> None:
        """Test log file rotation functionality."""
        # Create a logger with small max file size to trigger rotation
        rotation_logger = LoggerConfig(
            name="rotation_test",
            log_file=self.log_file,
            level=LogLevel.DEBUG,
            max_file_size=300,  # 300 bytes, between MIN_FILE_SIZE and MAX_FILE_SIZE
            backup_count=2
        ).create()

        try:
            # Write enough data to trigger multiple rotations
            for i in range(5):
                # Each message is 30 bytes (exceeds max_file_size)
                rotation_logger.info("X" * 30)
                time.sleep(0.1)  # Give some time for rotation to occur

            # Close handlers to ensure files are written
            rotation_logger.close_handlers()
            time.sleep(0.1)  # Wait a bit for file operations to complete

            # Verify main log file exists
            self.assertTrue(
                os.path.exists(self.log_file),
                "Main log file does not exist"
            )
            
            # Verify backup files exist (should have both .1 and .2 due to multiple rotations)
            backup_files = [f"{self.log_file}.{i}" for i in range(1, 3)]
            existing_backups = [f for f in backup_files if os.path.exists(f)]
            self.assertGreaterEqual(
                len(existing_backups),
                1,
                f"Expected at least one backup file, found {len(existing_backups)}"
            )

            # Verify file sizes
            for log_file in [self.log_file] + existing_backups:
                size = os.path.getsize(log_file)
                self.assertLessEqual(
                    size,
                    500,  # MAX_FILE_SIZE
                    f"Log file {log_file} exceeds maximum size: {size} bytes"
                )

        finally:
            rotation_logger.close_handlers()
            time.sleep(0.1)  # Wait before cleanup

    def test_invalid_logger_name(self) -> None:
        """Test validation of logger name."""
        with self.assertRaises(ValueError) as context:
            LoggerConfig(name="")
        self.assertIn("cannot be empty", str(context.exception))

        with self.assertRaises(ValueError) as context:
            LoggerConfig(name="   ")
        self.assertIn("cannot be empty", str(context.exception))

    def test_invalid_level(self) -> None:
        """Test validation of logging level."""
        with self.assertRaises(ValueError) as context:
            LoggerConfig(name="test", level="INFO")
        self.assertIn("must be a LogLevel enum value", str(context.exception))

    def test_invalid_file_size(self) -> None:
        """Test validation of max file size."""
        with self.assertRaises(ValueError) as context:
            LoggerConfig(name="test", max_file_size=100)  # Too small
        self.assertIn("must be between", str(context.exception))

        with self.assertRaises(ValueError) as context:
            LoggerConfig(name="test", max_file_size=1000 * 1024 * 1024)  # Too large
        self.assertIn("must be between", str(context.exception))

    def test_invalid_backup_count(self) -> None:
        """Test validation of backup count."""
        with self.assertRaises(ValueError) as context:
            LoggerConfig(name="test", backup_count=0)  # Too small
        self.assertIn("must be between", str(context.exception))

        with self.assertRaises(ValueError) as context:
            LoggerConfig(name="test", backup_count=20)  # Too large
        self.assertIn("must be between", str(context.exception))

    def test_invalid_email_config(self) -> None:
        """Test validation of email configuration."""
        invalid_config = {
            "mailhost": "smtp.example.com",
            "port": "not_a_number",  # Invalid port
            "fromaddr": "test@example.com",
            "toaddrs": ["test@example.com"],
            "subject": "Test",
            "username": "user",
            "password": "pass"
        }
        with self.assertRaises(ValueError) as context:
            LoggerConfig(name="test", email_config=invalid_config)
        self.assertIn("port must be a valid port number", str(context.exception))

        # Test missing required fields
        incomplete_config = {
            "mailhost": "smtp.example.com",
            "port": 587
        }
        with self.assertRaises(ValueError) as context:
            LoggerConfig(name="test", email_config=incomplete_config)
        self.assertIn("Missing required email configuration fields", str(context.exception))

    def test_config_update(self) -> None:
        """Test configuration update functionality."""
        logger_config = LoggerConfig(name="test_update")
        
        # Update level
        logger_config.update_config(level=LogLevel.DEBUG)
        self.assertEqual(logger_config.level, LogLevel.DEBUG)
        
        # Update file size
        new_size = 10 * 1024 * 1024
        logger_config.update_config(max_file_size=new_size)
        self.assertEqual(logger_config.max_file_size, new_size)
        
        # Update backup count
        logger_config.update_config(backup_count=5)
        self.assertEqual(logger_config.backup_count, 5)
        
        # Test invalid update
        with self.assertRaises(ValueError):
            logger_config.update_config(max_file_size=100)  # Too small

if __name__ == "__main__":
    unittest.main()
