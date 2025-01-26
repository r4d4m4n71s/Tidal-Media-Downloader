from mutagen.flac import FLAC
from mutagen import MutagenError
import os
from audio_codifier import *

def handle_flac_file(filepath):
    try:
        if not os.path.isfile(filepath):
            print(f"File does not exist: {filepath}")
            return

        if not filepath.lower().endswith('.flac'):
            print(f"Not a valid FLAC file: {filepath}")
            return
        
        # Choose the codec for re-encoding        
        # Create an instance of AudioProcessor
        processor = AudioCodifier(AudioCodec.FLAC)
        processor.reencode_audio(AudioCodec.FLAC, 'd:/Music/James Hype, Tita Lau/Vibrate - On The Ground (EP) [2024]/Vibrate-James Hype-[339462230-LOSSLESS].flac')
        
        audio = FLAC(filepath)
        print("FLAC file successfully loaded!")
        # Do something with the FLAC file
    except MutagenError as e:
        print(f"Error processing file '{filepath}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



# Example usage
file_path = 'd:/Music/James Hype, Tita Lau/Vibrate - On The Ground (EP) [2024]/Vibrate-James Hype-[339462230-LOSSLESS].flac'
handle_flac_file(file_path)

if __name__ == '__main__':
    # test()
    main()
