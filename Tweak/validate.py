import logging
from TidalAuthenticator import TidalAuthenticator
from TidalDiff import TidalDiff
from TidalFile import FileSystem
from TidalSubProcess import TidalSubProcess
from config import SESSION_FILE, FOLDER_PATH

def main():
    try:
        # Initialize TidalAuthenticator
        authenticator = TidalAuthenticator(SESSION_FILE)
        session = authenticator.authenticate()
        logging.info("TidalAuthenticator initialized successfully.")

        # Initialize TidalDiff
        tidal_diff = TidalDiff()
        logging.info("TidalDiff initialized successfully.")

        # Initialize FileSystem
        file_system = FileSystem(FOLDER_PATH)
        logging.info("FileSystem initialized successfully.")

        # Initialize TidalSubProcess
        tidal_sub_process = TidalSubProcess()
        logging.info("TidalSubProcess initialized successfully.")

        logging.info("All classes compiled and initialized successfully.")
    except Exception as e:
        logging.error(f"An error occurred during validation: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
