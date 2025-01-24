import subprocess
import logging
from TidalDiff import TidalDiff
from config import FOLDER_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TidalSubProcess:
    def __init__(self):
        """
        Initialize the TidalSubProcess class.
        """
        self.tidalDiff = TidalDiff()

    def run_command(self, command, skipStdout=False):
        """
        Run a command using subprocess and capture the output.

        :param command: List of command arguments.
        :return: Tuple containing stdout and stderr.
        """
        try:            
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,  # Capture standard output
                stderr=subprocess.PIPE,  # Capture standard error
                text=True                # Ensure output is in string format
            )

            if len(result.stdout) < 500:
                if "[ERR]" in result.stdout:
                    logging.error(f"Command '{command}' failed with error: {result.stdout}")
                    return None, result.stdout

            if skipStdout:               
                return "Success " + str(command), None
            else:
                return result.stdout, result.stderr
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Command '{command}' failed with error: {e}")
            return None, e
        except Exception as e:
            logging.error(f"An unexpected error occurred while running command '{command}': {e}")
            return None, e

    def export(self):
        """
        Export favorite tracks by running the tidal-dl command for each track ID.
        """
        try: 
            trackDiff = self.tidalDiff.get_favoritesTracksDiff(FOLDER_PATH)
            quality = list()
            
            quality.append(("tidal-dl", "-q", "HiFi"))
            quality.append(("tidal-dl", "-q", "High"))
            
            for trackId in trackDiff:
                logging.info(f"Processing track id: {trackId}")
                self.exec_command(["tidal-dl", "-q", "Master"])   
                if not self.exec_fallback_command(quality.copy(), ["tidal-dl", "-l", str(trackId)]):
                    logging.error(f"Unable to export {trackId}")            

            self.exec_command(["tidal-dl", "-q", "Master"])
        except Exception as e:
            logging.error(f"An unexpected error occurred while executing process : {e}")
            
    def exec_fallback_command(self, commandList, mainCommand):
        """
        Execute the main command and fallback to other commands if it fails.

        :param commandList: List of fallback commands.
        :param mainCommand: The main command to execute.
        :return: True if a command succeeds, False otherwise.
        """
        if not commandList:
            del commandList
            return False
        
        if not self.exec_command(mainCommand, True):
            fallback_command = commandList.pop(0)
            logging.info(f"Executing fallback command: {fallback_command}")
            self.exec_command(fallback_command)
            return self.exec_fallback_command(commandList, mainCommand)
        
        return True

    def exec_command(self, command, skipStdout=False):
        """
        Execute a command and log the output and errors.

        :param command: The command to execute.
        :return: True if the command succeeds, False otherwise.
        """        
        stdout, stderr = self.run_command(command, skipStdout)
        
        if stdout:
            logging.info("Command Output:")
            logging.info(stdout)
        if stderr:
            logging.error("Command Errors:")
            logging.error(stderr)
            return False
        
        return True
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    TidalSubProcess().export()