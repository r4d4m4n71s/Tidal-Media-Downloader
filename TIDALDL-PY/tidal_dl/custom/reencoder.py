import ffmpeg
import os
import json
from typing import List, Dict, Optional, Any
from .logger import Logger, LoggerConfig, LogLevel

import platform

def get_default_ffmpeg_path() -> str:
    """Get the default FFmpeg path based on the operating system."""
    if platform.system() == "Windows":
        return r"C:\ffmpeg\bin"
    elif platform.system() == "Darwin":  # macOS
        return "/usr/local/bin"
    else:  # Linux and others
        return "/usr/bin"

FFMPEG_PATH = os.environ.get("FFMPEG_PATH", get_default_ffmpeg_path())

class EncodingError(Exception):
    """Custom exception for processing errors."""
    pass

class Codec:
    """Configuration class for audio codecs."""
    def __init__(self, name: str, codec: str, ext: str, desc: str):
        self.name = name
        self.codec = codec
        self.ext = ext
        self.desc = desc

class Reencoder:
    """
    A class to handle encoding and metadata manipulation using FFmpeg.
    """

    @staticmethod
    def load_codecs(config_path: Optional[str] = None) -> Dict[str, Codec]:
        """
        Load codec configurations from a JSON file.

        Args:
            config_path: Optional path to the codec configuration file.
                      If not provided, uses the default _config/ffmpeg_codecs.json

        Returns:
            Dictionary of codec configurations mapped by name.

        Raises:
            FileNotFoundError: If the config file is missing
            json.JSONDecodeError: If the config file is invalid
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "_config", "ffmpeg_codecs.json")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            codec_data = json.load(f)
        
        codecs = {}
        for name, data in codec_data.items():
            codecs[name] = Codec(
                name=name,
                codec=data['codec'],
                ext=data['ext'],
                desc=data['description']
            )
        return codecs

    def __init__(self, codec: Codec, logger: Optional[Logger] = None, codecs_path: Optional[str] = None):
        """
        Initialize the Reencoder with the codec configuration.

        Args:
            codec: Codec configuration for re-encoding.
            logger: Optional logger instance. If not provided, creates a new one.
            codecs_path: Optional path to codecs configuration file.

        Raises:
            ValueError: If codec is None or invalid.
        """
        if codec is None:
            raise ValueError("Codec cannot be None")
        
        if not isinstance(codec, Codec):
            raise ValueError("Invalid codec type. Must be an instance of Codec")

        if FFMPEG_PATH not in os.environ.get("PATH", ""):
            os.environ["PATH"] += os.pathsep + FFMPEG_PATH

        self.codec = codec
        self.logger = logger or Logger(LoggerConfig(
            name=__name__,
            level=LogLevel.INFO
        ).create())
        
        # Load all available codecs for extension lookup
        self.available_codecs = self.load_codecs(codecs_path)

    def get_codec_from_extension(self, input_file: str) -> Codec:
        """
        Determine the codec from the file extension.

        Args:
            input_file: Path to the input file.

        Returns:
            The corresponding codec value.

        Raises:
            EncodingError: If the file extension is unsupported.
        """
        extension = os.path.splitext(input_file)[1].lower()
        
        # First check if it matches the current codec
        if extension == self.codec.ext.lower():
            return self.codec
            
        # Then check all available codecs
        for codec in self.available_codecs.values():
            if extension == codec.ext.lower():
                return codec
                
        raise EncodingError(f"Unsupported file extension: {extension}")

    def _generate_unique_output_path(self, base_path: str, extension: str) -> str:
        """
        Generate a unique output path that doesn't exist.

        Args:
            base_path: Base path without extension
            extension: File extension including the dot

        Returns:
            A unique file path that doesn't exist
        """
        counter = 0
        while True:
            if counter == 0:
                path = f"{base_path}_Tagged{extension}"
            else:
                path = f"{base_path}_Tagged_{counter}{extension}"
            if not os.path.exists(path):
                return path
            counter += 1

    def _validate_metadata_tags(self, metadata_tags: Optional[List[str]]) -> None:
        """
        Validate metadata tags are strings and not empty.

        Args:
            metadata_tags: List of metadata tags to validate

        Raises:
            ValueError: If any tag is invalid
        """
        if metadata_tags:
            if not all(isinstance(tag, str) for tag in metadata_tags):
                raise ValueError("All metadata tags must be strings")
            if any(not tag.strip() for tag in metadata_tags):
                raise ValueError("Metadata tags cannot be empty strings")

    def get_metadata(self, file_path: str) -> dict:
        """
        Get metadata of the file.

        Args:
            file_path: Path to the file.

        Returns:
            Metadata of the file.

        Raises:
            ffmpeg.Error: If metadata retrieval fails
        """
        try:
            return ffmpeg.probe(file_path)
        except ffmpeg.Error as e:
            error_message = e.stderr.decode('utf-8')
            self.logger.error(f"Error retrieving metadata for {file_path}: {error_message}")
            raise
    
    def reencode(
        self,
        file_path: str,
        output_path: Optional[str] = None,
        codec: Optional[Codec] = None,
        delete_original: bool = False,
        metadata_tags: Optional[List[str]] = None,
        remove_all_tags: bool = False,
        output_options: Optional[Dict[str, str]] = None,
        ffmpeg_global_options: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Re-encode the file to the specified codec and optionally modify metadata.

        Args:
            file_path: Path to the input file
            output_path: Optional path for the output file
            codec: Optional codec to use (defaults to codec from file extension)
            delete_original: Whether to delete the original file after encoding
            metadata_tags: List of metadata tags to modify (format: "key=value")
            remove_all_tags: Whether to remove all metadata tags
            output_options: Additional FFmpeg output options
            ffmpeg_global_options: Additional FFmpeg global options

        Returns:
            Path to the output file if successful, None otherwise

        Raises:
            EncodingError: If encoding fails
        """
        # Validate inputs
        if not codec:
            codec = self.get_codec_from_extension(file_path)

        if not os.path.isfile(file_path):
            self.logger.error(f"File does not exist: {file_path}")
            return None

        # Validate metadata tags
        self._validate_metadata_tags(metadata_tags)

        # Generate default output path if not provided
        if output_path is None:
            base_name, _ = os.path.splitext(file_path)
            output_path = self._generate_unique_output_path(base_name, self.codec.ext)

        try:
            # Initialize ffmpeg chain
            stream = ffmpeg.input(file_path)

            # Start with base options
            output_command = {
                'acodec': self.codec.codec,
                'map': '0:a'  # Always map audio stream
            }

            # Handle metadata
            metadata_args = []
            if remove_all_tags:
                metadata_args.extend(['-map_metadata', '-1'])
            elif metadata_tags:
                # Process metadata tags
                for tag in metadata_tags:
                    if '=' in tag:
                        key, value = tag.split('=', 1)
                        metadata_args.extend(['-metadata', f'{key}={value}'])
                    else:
                        # If no value provided, remove the tag
                        metadata_args.extend(['-metadata', f'{tag}='])

            # Process user-provided output options
            if output_options:
                output_command.update(output_options)

            # Special handling for m4a output
            if self.codec.ext.lower() == '.m4a':
                output_command['f'] = 'mp4'  # Force MP4 container format

            # Create output stream
            ffmpeg_command = ffmpeg.output(stream, output_path, **output_command)

            # Apply metadata arguments first
            if metadata_args:
                ffmpeg_command = ffmpeg_command.global_args(*metadata_args)

            # Apply user-provided global options
            if ffmpeg_global_options:
                global_args = []
                for key, value in ffmpeg_global_options.items():
                    if value is not None:
                        global_args.extend([f'-{key}', str(value)])
                if global_args:
                    ffmpeg_command = ffmpeg_command.global_args(*global_args)
            
            # Add overwrite flag
            if delete_original and file_path == output_path:
                ffmpeg_command = ffmpeg_command.overwrite_output()
                        
            self.logger.debug(f"Executing FFmpeg command for: {file_path}")
            ffmpeg_command.run()

            self.logger.info(f"Successfully re-encoded: {output_path}")

            # Optionally delete the original file
            if delete_original and file_path != output_path:
                try:
                    os.remove(file_path)
                    self.logger.debug(f"Deleted original file: {file_path}")
                except OSError as e:
                    self.logger.warning(f"Failed to delete original file {file_path}: {str(e)}")

        except ffmpeg.Error as e:
            # Handle FFmpeg-specific errors
            stderr = e.stderr.decode('utf-8') if hasattr(e, 'stderr') and e.stderr else str(e.decode('utf-8'))
            stdout = e.stdout.decode('utf-8') if hasattr(e, 'stdout') and e.stdout else ''
            error_detail = f"{stderr}\n{stdout}".strip() or str(e)
            self.logger.error(f"FFmpeg error during re-encoding of {file_path}:\n{error_detail}")
            raise EncodingError(f"FFmpeg error re-encoding {file_path}: {error_detail}") from e
        except OSError as e:
            # Handle file system related errors
            self.logger.error(f"File system error during re-encoding of {file_path}: {e}")
            raise EncodingError(f"File system error re-encoding {file_path}: {e}") from e
        except Exception as e:
            # Handle any other unexpected errors
            self.logger.error(f"Unexpected error during re-encoding of {file_path}: {e}")
            raise EncodingError(f"Unexpected error re-encoding {file_path}: {e}") from e

        return output_path