import os
import re
import logging

class FileSystem:
    """
    A class to handle file system operations related to Tidal tracks.
    """

    # Regex pattern constant to match {TrackTitle}{ExplicitFlag}-{ArtistName}-[{TrackID}-{AudioQuality}].fileExtension
    PATTERN = r"\[(\d+)-[^\]]+\]\.\w{3,4}$"

    def __init__(self, folder_path):
        """
        Initialize the FileSystem with the given folder path.
        """
        self.folder_path = folder_path

    def extract_track_id_from_filename(self, filename):
        """
        Extract the track ID from the given filename using regex.
        """
        match = re.search(self.PATTERN, filename)
        if match:
            return match.group(1)
        return None

    def find_notFoundTracksIds(self, track_ids):
        """
        Find track IDs that are not found in the folder path.

        :param track_ids: List of track IDs to check.
        :return: Set of track IDs that are not found in the files.
        """
        found_track_ids = set()
               
        try:
            # Walk through the directory
            for root, dirs, files in os.walk(self.folder_path):
                for file_name in files:
                    # Extract TrackID from the file name using regex
                    track_id = self.extract_track_id_from_filename(file_name)
                    
                    # If TrackID is in the provided list, add to found IDs
                    if track_id: 
                        int_track_ids = int(track_id)
                        if  int_track_ids in track_ids:
                            found_track_ids.add(int_track_ids)

        except Exception as e:
            logging.error(f"An error occurred while searching for track IDs: {e}")
                    
        # Calculate the not found TrackIDs
        not_found_track_ids = set(track_ids) - found_track_ids
        return not_found_track_ids