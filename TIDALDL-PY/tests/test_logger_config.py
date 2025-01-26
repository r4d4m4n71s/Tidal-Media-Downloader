import os
import sys
import unittest

# Adjust the path to include the directory containing the logger_config module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../tidal_dl/custom')))
from logger import *


class TestLoggerConfig(unittest.TestCase):

    def setUp(self):
        self.log_file = "tests/test_logs/app.log"
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self.logger_config = LoggerConfig(name="test_logger", log_file=self.log_file, level=LogLevel.DEBUG)
        self.logger = self.logger_config.get_logger()

    def tearDown(self):
        # Close all handlers associated with the logger
        self.logger_config._close_handlers()
        if os.path.isfile(self.log_file):
            os.remove(self.log_file)

    def test_logging_info(self):
        self.logger.info("This is an info message")
        self.logger_config._close_handlers()  # Ensure handlers are closed before reading the file
        with open(self.log_file, "r") as f:
            log_content = f.read()
        self.assertIn("INFO", log_content)
        self.assertIn("This is an info message", log_content)

    def test_logging_warning(self):
        self.logger.warning("This is a warning message")
        self.logger_config._close_handlers()  # Ensure handlers are closed before reading the file
        with open(self.log_file, "r") as f:
            log_content = f.read()
        self.assertIn("WARNING", log_content)
        self.assertIn("This is a warning message", log_content)

    def test_logging_error(self):
        self.logger.error("This is an error message")
        self.logger_config._close_handlers()  # Ensure handlers are closed before reading the file
        with open(self.log_file, "r") as f:
            log_content = f.read()
        self.assertIn("ERROR", log_content)
        self.assertIn("This is an error message", log_content)

    # def test_console_handler_colors(self):
    #     # Redirect stdout to capture console output
    #     console_output = StringIO()
    #     console_handler = logging.StreamHandler(console_output)
    #     console_handler.setFormatter(ColorFormatter("%(levelname)s - %(message)s"))
    #     self.logger.addHandler(console_handler)

    #     # Log messages with different levels
    #     self.logger.debug("Debug message")
    #     self.logger.info("Info message")
    #     self.logger.warning("Warning message")
    #     self.logger.error("Error message")
    #     self.logger.critical("Critical message")

    #     # Flush and remove the console handler
    #     console_handler.flush()
    #     self.logger.removeHandler(console_handler)

    #     # Get the console output
    #     output = console_output.getvalue()
    #     console_output.close()

    #     # Check for color codes in the output
    #     self.assertIn("\033[94mDEBUG - Debug message\033[0m", output)  # Blue
    #     self.assertIn("\033[92mINFO - Info message\033[0m", output)    # Green
    #     self.assertIn("\033[93mWARNING - Warning message\033[0m", output)  # Yellow
    #     self.assertIn("\033[91mERROR - Error message\033[0m", output)  # Red
    #     self.assertIn("\033[95mCRITICAL - Critical message\033[0m", output)  # Magenta

if __name__ == "__main__":
    unittest.main()
