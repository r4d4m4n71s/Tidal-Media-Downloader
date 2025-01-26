import ffmpeg
import os
from enum import Enum
from logger import *

# Set FFmpeg path explicitly
FFMPEG_PATH = r"C:\ffmpeg\bin"


class AudioCodec(Enum):
    flac    =  "flac"
    mp3     =   "libmp3lame"
    aac     =   "aac"
    opus    =  "libopus"
    wav     =   "pcm_s16le"

    # def __init__(self, codec_name, file_extension):
    #     self.codec_name = codec_name
    #     self.file_extension = file_extension

class AudioProcessingError(Exception):
    """Custom exception for audio processing errors."""
    pass

class AudioCodifier:
    
    def __init__(self):
        if FFMPEG_PATH not in os.environ.get("PATH", ""):
            os.environ["PATH"] += os.pathsep + FFMPEG_PATH

    def get_codec_from_extension(self, input_file):
        # Logic to determine codec from file extension
        extension = os.path.splitext(input_file)[1].lower()
        if extension == '.mp3':
            return AudioCodec.mp3
        elif extension == '.aac':
            return AudioCodec.aac
        elif extension == '.flac':
            return AudioCodec.flac
        elif extension == '.wav':
            return AudioCodec.wav
        else:
            raise AudioProcessingError(f"Unsupported file extension: {extension}")        

    def reencode_audio(self, input_file, output_directory=None, codec: AudioCodec=None, delete_original=False):
        
        if not codec:
            codec = self.get_codec_from_extension(input_file)
        
        if not os.path.isfile(input_file):
            logger.error(f"File does not exist: {input_file}")
            return None

        if not output_directory:
            output_directory = os.path.dirname(input_file)
        
        output_file = os.path.join(
            output_directory,
            f"{os.path.splitext(os.path.basename(input_file))[0]}.{codec.name}"
        )

        try:
            # Use ffmpeg to re-encode the file
            logger.info(f"Metadata before re-encoding: {ffmpeg.probe(input_file)}")
            ffmpeg.input(input_file).output(output_file, acodec=codec.value).run(overwrite_output=True)
            logger.info(f"Successfully re-encoded: {input_file} -> {output_file}")
            logger.info(f"Metadata after re-encoding: {ffmpeg.probe(output_file)}")
            
            if delete_original and input_file != output_file:
                os.remove(input_file)

        except ffmpeg.Error as e:
            raise AudioProcessingError(f"Error re-encoding {input_file}") from e

        return output_file    

    def get_metadata(self, file_path):
        return ffmpeg.probe(file_path)