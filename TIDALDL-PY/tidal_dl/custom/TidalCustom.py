import tidalapi
import logging

from Custom.TidalFile import FileFunctions
from Custom.TidalAuthenticator import TidalAuthenticator
from typing import Optional, Set
from settings import *
from tidal import *
from download import *
from datetime import datetime

class TidalFunctions:
    def __init__(self):
        self.session = self.authenticate()

    def authenticate(self) -> Optional[tidalapi.Session]:
        authenticator = TidalAuthenticator()
        try:
            session = authenticator.authenticate()
            logging.info(f"Token expires on: {datetime.fromtimestamp(session.expiry_time).strftime("%Y-%m-%d %H:%M:%S")}")
            return session
        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            return None

    def start_favorite_tracks(self):
       
        try: 
            trackDiff = self.get_favoritesTracksDiff()
            
            # Define the quality levels to try
            quality = list()            
            quality.append(AudioQuality.Max)
            quality.append(AudioQuality.Master)
            quality.append(AudioQuality.HiFi)
            quality.append(AudioQuality.High)
            quality.append(AudioQuality.Normal)            
        
            album = None

            for trackId in trackDiff:
                logging.info(f"Processing track id: {trackId}")
                
                etype, obj = TIDAL_API.getByString(str(trackId))
                                                
                if album is None or album.id != obj.album.id:
                    album = TIDAL_API.getAlbum(obj.album.id) 
                    if SETTINGS.saveCovers:
                        downloadCover(album)
                
                # try to download the track at the highest quality level
                self.getTrack_fallback(obj, album, quality)                

        except Exception as e:
            logging.error(f"An unexpected error occurred while executing process : {e}")


    def getTrack_fallback(self, obj, album, qualityList):
        # running fallback quality levels
        logging.error(f"Fallgack track {obj.title} - {obj.id} - {obj.album.title} - {obj.album.id}")            
        error = None
        for quality in qualityList:
            success, error = downloadTrack(track=obj, album=album, audioQuality=quality)
            if success:
                return True

        logging.error(f"Unable to export at any quality level:{error}")            
        return False 


    def get_favoritesTracksDiff(self) -> Optional[Set[str]]:
        if self.session:
            try:
                favorites = self.session.user.favorites.tracks()
                file_system = FileFunctions(SETTINGS.downloadPath)
                return file_system.find_notFoundTracksIds([track.id for track in favorites])
            except Exception as e:
                logging.error(f"Failed to get favorite tracks: {e}")
                return None
        else:
            logging.error("No active session. Cannot retrieve favorite tracks.")
            return None