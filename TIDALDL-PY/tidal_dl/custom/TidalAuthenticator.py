import tidalapi
import json
import logging
import os
from settings import *

class TidalAuthenticator:
    def __init__(self, session_filePath=SETTINGS.sessionFilePath):
        self.session = tidalapi.Session()
        self.session_file = os.path.join(os.path.dirname(__file__), session_filePath)

    def authenticate(self):
        try:
            if not self._load_session_from_file():
                self._login_oauth_simple()
                self._save_session_to_file()
            return self.session

        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            raise Exception(f"Authentication failed: {e}")

    def _load_session_from_file(self):
        """
        Load the session from the JSON file.

        :return: True if the session was loaded successfully, False otherwise.
        """
        try:
            with open(self.session_file, 'r') as file:
                session_data = json.load(file)

            token_type = session_data.get('token_type')
            access_token = session_data.get('access_token')
            refresh_token = session_data.get('refresh_token')
            expiry_time = session_data.get('expiry_time')

            if not all([token_type, access_token, refresh_token, expiry_time]):
                logging.warning("Session file is missing some fields.")
                return False

            self.session.load_oauth_session(token_type, access_token, refresh_token, expiry_time)
            logging.info("Session loaded successfully from file.")
            return True

        except FileNotFoundError:
            logging.warning("Session file not found.")
            return False
        except json.JSONDecodeError:
            logging.error("Error decoding session file.")
            return False

    def _login_oauth_simple(self):
        """
        Log in using `login_oauth_simple()` and print the OAuth URL for the user to authenticate.
        """
        logging.info("Please authenticate with Tidal:")
        self.session.login_oauth_simple()
        logging.info("Authentication successful.")

    def _save_session_to_file(self):
        """
        Save the current session to the JSON file.
        """
        session_data = {
            "token_type": self.session.token_type,
            "access_token": self.session.access_token,
            "refresh_token": self.session.refresh_token,
            "expiry_time": self.session.expiry_time.timestamp().strftime('%Y-%j %H:%M:%S'),
            "country_code": self.session.country_code,
            "session_id": self.session.session_id
        }
        try:
            with open(self.session_file, 'w') as file:
                json.dump(session_data, file, indent=4)
            logging.info("Session saved to file successfully.")
        except Exception as e:
            logging.error(f"Failed to save session to file: {e}")