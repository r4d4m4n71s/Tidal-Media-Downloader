import tidalapi
from datetime import datetime
from TidalFile import FileSystem
from TidalAuthenticator import TidalAuthenticator
import logging
from typing import List, Optional, Set
from config import SESSION_FILE

class TidalDiff:
    def __init__(self):
        self.session = self.authenticate()

    def authenticate(self) -> Optional[tidalapi.Session]:
        authenticator = TidalAuthenticator(SESSION_FILE)
        try:
            session = authenticator.authenticate()
            logging.info(f"Token expires on: {datetime.fromtimestamp(session.expiry_time).strftime('%Y-%j %H:%M:%S')}")
            return session
        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            return None

    def get_favoritesTracksDiff(self, folder_path: str) -> Optional[Set[str]]:
        if self.session:
            try:
                favorites = self.session.user.favorites.tracks()
                file_system = FileSystem(folder_path)
                return file_system.find_notFoundTracksIds([track.id for track in favorites])
            except Exception as e:
                logging.error(f"Failed to get favorite tracks: {e}")
                return None
        else:
            logging.error("No active session. Cannot retrieve favorite tracks.")
            return None