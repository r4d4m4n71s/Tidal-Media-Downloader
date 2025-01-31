import os
import json
from typing import Tuple, List, Dict, Any
from mutagen.flac import FLAC, Picture
from mutagen.mp3 import MP3
from mutagen.id3 import APIC, USLT, ID3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.wave import WAVE
from mutagen.aac import AAC
from deepdiff import DeepDiff

class AudioFormatError(Exception):
    """Custom exception for audio format related errors."""
    pass

class MetadataError(Exception):
    """Custom exception for metadata related errors."""
    pass

class AudioMetadataUpdater:
    """Class for updating metadata in various audio file formats."""

    # Supported file formats and their corresponding classes
    SUPPORTED_FORMATS = {
        '.flac': (FLAC, 'FLAC audio'),
        '.mp3': (MP3, 'MP3 audio'),
        '.mp4': (MP4, 'MP4 audio'),
        '.m4a': (MP4, 'M4A audio'),
        '.wav': (WAVE, 'WAV audio'),
        '.aac': (AAC, 'AAC audio')
    }

    # Common MIME types
    MIME_TYPES = {
        'jpeg': 'image/jpeg',
        'png': 'image/png'
    }

    def __init__(self, file_path: str, tags_path: str):
        """
        Initialize the AudioMetadataUpdater with the file path.

        Args:
            file_path: Path to the audio file
            tags_path: Path to the tags mapping file

        Raises:
            FileNotFoundError: If either file doesn't exist
            AudioFormatError: If the audio format is unsupported
            MetadataError: If tag mappings can't be loaded
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        if not os.path.exists(tags_path):
            raise FileNotFoundError(f"Tags mapping file not found: {tags_path}")

        self.file_path = file_path
        self.audio = None
        self.tags_path = tags_path
        
        try:
            self.mp3_tags, self.mp4_tags = self._load_tag_mappings(tags_path)
        except (json.JSONDecodeError, KeyError) as e:
            raise MetadataError(f"Failed to load tag mappings: {str(e)}")

    def _get_file_format(self) -> Tuple[str, Any]:
        """
        Get the file format and corresponding audio class.

        Returns:
            Tuple containing the extension and audio class

        Raises:
            AudioFormatError: If the format is unsupported
        """
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise AudioFormatError(
                f"Unsupported audio format: {ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS.keys())}"
            )
        return ext, self.SUPPORTED_FORMATS[ext][0]

    def _load_audio_file(self) -> Any:
        """
        Load the audio file based on its extension.

        Returns:
            The appropriate mutagen audio object

        Raises:
            AudioFormatError: If loading fails
        """
        try:
            ext = os.path.splitext(self.file_path)[1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                raise AudioFormatError(
                    f"Unsupported audio format: {ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS.keys())}"
                )
            
            if ext == '.mp3':
                audio = MP3(self.file_path, ID3=ID3)
                if audio.tags is None:
                    audio.add_tags()
                return audio
            elif ext in ['.mp4', '.m4a']:
                return MP4(self.file_path)
            elif ext == '.flac':
                return FLAC(self.file_path)
            elif ext == '.wav':
                return WAVE(self.file_path)
            elif ext == '.aac':
                audio = AAC(self.file_path)
                if audio.tags is None:
                    audio.add_tags()
                return audio
            else:
                raise AudioFormatError(f"Unsupported audio format: {ext}")
                
        except Exception as e:
            if isinstance(e, AudioFormatError):
                raise
            if isinstance(e, FileNotFoundError):
                raise
            raise AudioFormatError(f"Failed to load audio file: {str(e)}")

    def _load_tag_mappings(self, tags_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Load tag mappings from a JSON file.

        Args:
            tags_path: Path to the JSON file containing tag mappings

        Returns:
            Tuple containing tag mappings for MP3 and MP4 files

        Raises:
            MetadataError: If mappings can't be loaded or are invalid
        """
        try:
            with open(tags_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate required sections
            if not all(key in data for key in ['mp3_tags', 'mp4_tags']):
                raise MetadataError("Missing required sections in tag mappings file")

            # Validate tag mapping structure
            for section in ['mp3_tags', 'mp4_tags']:
                for tag, mapping in data[section].items():
                    if section == 'mp3_tags' and 'mutagen_frame' not in mapping:
                        raise MetadataError(f"Missing mutagen_frame for MP3 tag: {tag}")
                    if section == 'mp4_tags' and 'mutagen_key' not in mapping:
                        raise MetadataError(f"Missing mutagen_key for MP4 tag: {tag}")

            # Cache the mappings
            self._mp3_tag_cache = data['mp3_tags']
            self._mp4_tag_cache = data['mp4_tags']

            return self._mp3_tag_cache, self._mp4_tag_cache

        except json.JSONDecodeError as e:
            raise MetadataError(f"Invalid JSON in tag mappings file: {str(e)}")
        except KeyError as e:
            raise MetadataError(f"Missing required key in tag mappings: {str(e)}")
        except Exception as e:
            raise MetadataError(f"Failed to load tag mappings: {str(e)}")

    def update_metadata_list(self, metadata_list: List[Tuple[str, Any]], encoding: int = 3, lang: str = 'eng') -> None:
        """
        Update or add a list of metadata to the audio file.

        Args:
            metadata_list: List of tuples containing metadata key and value
            encoding: The encoding to use for the metadata (1-4)
            lang: The language code to use for the metadata (ISO 639-2)

        Raises:
            ValueError: If metadata_list is invalid or empty
            MetadataError: If metadata update fails
        """
        # Validate metadata list
        if not metadata_list:
            raise ValueError("Metadata list cannot be empty")

        if not isinstance(metadata_list, (list, tuple)):
            raise ValueError("Metadata list must be a list or tuple")

        if not all(isinstance(item, (list, tuple)) and len(item) == 2 for item in metadata_list):
            raise ValueError("Each metadata item must be a (key, value) tuple")

        # Validate encoding
        if not isinstance(encoding, int):
            raise ValueError("Encoding must be an integer")
        if not 1 <= encoding <= 4:
            raise ValueError("Encoding must be between 1 and 4")

        # Validate language code
        if not isinstance(lang, str):
            raise ValueError("Language code must be a string")
        if not lang.isalpha() or len(lang) != 3:
            raise ValueError("Language code must be a 3-letter ISO 639-2 code")
        if not lang.islower():
            lang = lang.lower()

        try:
            for key, value in metadata_list:
                self.update_or_add_metadata(key, value, encoding, lang)
            #self.audio.save()
        except Exception as e:
            raise MetadataError(f"Failed to update metadata list: {str(e)}")

    def update_or_add_metadata(self, key: str, value: Any, encoding: int = 3, lang: str = 'eng') -> None:
        """
        Update or add metadata to the audio file.

        Args:
            key: The metadata key (e.g., 'title', 'album', 'copyright')
            value: The value to set for the key
            encoding: The encoding to use for the metadata (1-4)
            lang: The language code to use for the metadata (ISO 639-2)

        Raises:
            ValueError: If key or value is invalid
            MetadataError: If metadata update fails
            AudioFormatError: If audio format is unsupported
            FileNotFoundError: If required files are not found
        """
        # Validate key
        if not key or not isinstance(key, str):
            raise ValueError("Metadata key must be a non-empty string")

        # Validate encoding
        if not isinstance(encoding, int) or not 1 <= encoding <= 4:
            raise ValueError("Encoding must be an integer between 1 and 4")

        # Validate language code
        if not isinstance(lang, str) or not lang.isalpha() or len(lang) != 3:
            raise ValueError("Language code must be a 3-letter ISO 639-2 code")

        # Handle string values
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return

        # Normalize key to lowercase
        key = key.lower()

        try:
            # Load audio file if not already loaded
            if self.audio is None:
                self.audio = self._load_audio_file()

            # Get file extension to determine audio type
            ext = os.path.splitext(self.file_path)[1].lower()
            
            # Update based on file type
            if ext == '.flac':
                self._update_flac_metadata(key, value)
            elif ext == '.mp3':
                self._update_mp3_metadata(key, value, encoding, lang)
            elif ext in ['.mp4', '.m4a']:
                self._update_mp4_metadata(key, value)
            elif ext == '.wav':
                self._update_wave_metadata(key, value)
            elif ext == '.aac':
                self._update_aac_metadata(key, value)
            else:
                raise AudioFormatError(f"Unsupported audio format: {ext}")

            # Save changes
            self.audio.save()

        except (ValueError, FileNotFoundError, AudioFormatError) as e:
            raise
        except Exception as e:
            raise MetadataError(f"Failed to update metadata '{key}': {str(e)}")

    
    def _update_flac_metadata(self, key: str, value: Any, cover_path: str = None) -> None:
        """
        Update or add metadata for FLAC files.

        Args:
            key: The metadata key
            value: The value to set for the key
            cover_path: Optional path to cover art image file

        Raises:
            MetadataError: If metadata update fails
            FileNotFoundError: If cover art file is not found
            ValueError: If value type is invalid
        """
        if key == 'cover_art':
            image_path = cover_path or value
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Cover art file not found: {image_path}")
            
            try:
                picture = Picture()
                with open(image_path, 'rb') as f:
                    picture.data = f.read()
                
                # Try to determine MIME type from file extension
                ext = os.path.splitext(image_path)[1].lower()
                if ext in ['.jpg', '.jpeg']:
                    picture.mime = self.MIME_TYPES['jpeg']
                elif ext == '.png':
                    picture.mime = self.MIME_TYPES['png']
                else:
                    raise MetadataError(f"Unsupported image format: {ext}")
                    
                self.audio.add_picture(picture)
            except IOError as e:
                raise MetadataError(f"Failed to read cover art file: {str(e)}")
        else:
            # Validate value type for FLAC metadata
            if not isinstance(value, (str, list, bool, int, float)):
                raise ValueError(f"Invalid value type for FLAC metadata: {type(value)}")
            
            # Convert non-string/list values to string
            if isinstance(value, (bool, int, float)):
                value = str(value)
            
            try:
                self.audio[key] = value
            except Exception as e:
                raise MetadataError(f"Failed to set FLAC metadata '{key}': {str(e)}")
    def _update_mp3_metadata(self, key: str, value: Any, encoding: int = 3, lang: str = 'eng', cover_path: str = None) -> None:
        """
        Update or add metadata for MP3 files.

        Args:
            key: The metadata key
            value: The value to set for the key
            encoding: The encoding to use for the metadata (1-4)
            lang: The language code to use for the metadata (ISO 639-2)
            cover_path: Optional path to cover art image file

        Raises:
            MetadataError: If metadata update fails
            FileNotFoundError: If cover art file is not found
            ValueError: If value type is invalid or tag is unsupported
        """
        try:
            # Ensure tags exist
            if not hasattr(self.audio, 'tags') or self.audio.tags is None:
                self.audio.add_tags()

            # Validate encoding and language
            if not isinstance(encoding, int) or not 1 <= encoding <= 4:
                raise ValueError("Encoding must be an integer between 1 and 4")
            if not isinstance(lang, str) or not lang.isalpha() or len(lang) != 3:
                raise ValueError("Language code must be a 3-letter ISO 639-2 code")

            if key == 'cover_art':
                self._handle_cover_art(value, cover_path, encoding)
            else:
                # Convert value to string if needed
                if isinstance(value, (bool, int, float)):
                    value = str(value)
                elif not isinstance(value, str):
                    raise ValueError(f"Invalid value type for MP3 metadata: {type(value)}")

                if key in self._mp3_tag_cache:
                    self._add_standard_mp3_tag(key, value, encoding, lang)
                else:
                    self._add_custom_mp3_tag(key, value, encoding, lang)

        except Exception as e:
            if isinstance(e, (ValueError, FileNotFoundError)):
                raise
            raise MetadataError(f"Failed to update MP3 metadata '{key}': {str(e)}")

    def _handle_cover_art(self, value: str, cover_path: str = None, encoding: int = 3) -> None:
        """Handle cover art updates for audio files."""
        image_path = cover_path or value
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Cover art file not found: {image_path}")

        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            ext = os.path.splitext(image_path)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                mime = self.MIME_TYPES['jpeg']
            elif ext == '.png':
                mime = self.MIME_TYPES['png']
            else:
                raise MetadataError(f"Unsupported image format: {ext}")

            self.audio.tags.add(APIC(
                encoding=encoding,
                mime=mime,
                type=3,  # Cover (front)
                desc='Cover',
                data=image_data
            ))
        except IOError as e:
            raise MetadataError(f"Failed to read cover art file: {str(e)}")

    def _add_standard_mp3_tag(self, key: str, value: str, encoding: int, lang: str) -> None:
        """Add a standard MP3 tag using the tag mapping."""
        try:
            module_name, class_name = self._mp3_tag_cache[key]['mutagen_frame'].rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            frame_class = getattr(module, class_name)

            if not frame_class:
                raise ValueError(f"Invalid frame class for tag: {key}")

            if key == 'lyrics':
                self.audio.tags.add(frame_class(encoding=encoding, lang=lang, desc='', text=value))
            else:
                self.audio.tags.add(frame_class(encoding=encoding, text=value))
        except (ImportError, AttributeError) as e:
            raise MetadataError(f"Failed to load frame class for tag '{key}': {str(e)}")

    def _add_custom_mp3_tag(self, key: str, value: str, encoding: int, lang: str) -> None:
        """Add a custom MP3 tag using USLT frame."""
        try:
            self.audio.tags.add(USLT(encoding=encoding, lang=lang, desc=key, text=value))
        except Exception as e:
            raise MetadataError(f"Failed to add custom MP3 tag '{key}': {str(e)}")

    def _update_mp4_metadata(self, key: str, value: Any, cover_path: str = None) -> None:
        """
        Update or add metadata for MP4 files.

        Args:
            key: The metadata key
            value: The value to set for the key
            cover_path: Optional path to cover art image file

        Raises:
            MetadataError: If metadata update fails
            FileNotFoundError: If cover art file is not found
            ValueError: If value type is invalid
        """
        try:
            if key == 'cover_art':
                image_path = cover_path or value
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Cover art file not found: {image_path}")

                try:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()

                    # Determine image format from file extension
                    ext = os.path.splitext(image_path)[1].lower()
                    if ext in ['.jpg', '.jpeg']:
                        image_format = MP4Cover.FORMAT_JPEG
                    elif ext == '.png':
                        image_format = MP4Cover.FORMAT_PNG
                    else:
                        raise MetadataError(f"Unsupported image format: {ext}")

                    self.audio['covr'] = [MP4Cover(image_data, imageformat=image_format)]
                except IOError as e:
                    raise MetadataError(f"Failed to read cover art file: {str(e)}")
            else:
                # Convert value to appropriate type for MP4
                if isinstance(value, (bool, int, float)):
                    value = str(value)
                elif not isinstance(value, (str, list)):
                    raise ValueError(f"Invalid value type for MP4 metadata: {type(value)}")

                if key in self._mp4_tag_cache:
                    mutagen_key = self._mp4_tag_cache[key]['mutagen_key']
                    try:
                        self.audio[mutagen_key] = value
                    except Exception as e:
                        raise MetadataError(f"Failed to set MP4 tag '{key}' with key '{mutagen_key}': {str(e)}")
                else:
                    # Dynamically add a new tag for unsupported keys
                    try:
                        self.audio[f'----:com.apple.iTunes:{key}'] = value.encode('utf-8') if isinstance(value, str) else value
                    except Exception as e:
                        raise MetadataError(f"Failed to add custom MP4 tag '{key}': {str(e)}")

        except Exception as e:
            raise MetadataError(f"Failed to update MP4 metadata '{key}': {str(e)}")

    def _update_wave_metadata(self, key: str, value: Any, cover_path: str = None) -> None:
        """
        Update or add metadata for WAV files.

        Args:
            key: The metadata key
            value: The value to set for the key
            cover_path: Optional path to cover art image file

        Raises:
            MetadataError: If metadata update fails
            FileNotFoundError: If cover art file is not found
            ValueError: If value type is invalid
        """
        try:
            if key == 'cover_art':
                picture = Picture()
                image_path = cover_path or value
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Cover art file not found: {image_path}")

                try:
                    with open(image_path, 'rb') as f:
                        picture.data = f.read()

                    # Determine MIME type from file extension
                    ext = os.path.splitext(image_path)[1].lower()
                    if ext in ['.jpg', '.jpeg']:
                        picture.mime = self.MIME_TYPES['jpeg']
                    elif ext == '.png':
                        picture.mime = self.MIME_TYPES['png']
                    else:
                        raise MetadataError(f"Unsupported image format: {ext}")

                    self.audio.add_picture(picture)
                except IOError as e:
                    raise MetadataError(f"Failed to read cover art file: {str(e)}")
            else:
                # Validate and convert value
                if isinstance(value, (bool, int, float)):
                    value = str(value)
                elif not isinstance(value, str):
                    raise ValueError(f"Invalid value type for WAV metadata: {type(value)}")

                self.audio[key] = value

        except Exception as e:
            raise MetadataError(f"Failed to update WAV metadata '{key}': {str(e)}")

    def _update_aac_metadata(self, key: str, value: Any, cover_path: str = None) -> None:
        """
        Update or add metadata for AAC files.

        Args:
            key: The metadata key
            value: The value to set for the key
            cover_path: Optional path to cover art image file

        Raises:
            MetadataError: If metadata update fails
            FileNotFoundError: If cover art file is not found
            ValueError: If value type is invalid
        """
        try:
            if not hasattr(self.audio, 'tags') or self.audio.tags is None:
                self.audio.add_tags()

            if key == 'cover_art':
                image_path = cover_path or value
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Cover art file not found: {image_path}")

                try:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()

                    # Determine image format from file extension
                    ext = os.path.splitext(image_path)[1].lower()
                    if ext in ['.jpg', '.jpeg']:
                        image_format = MP4Cover.FORMAT_JPEG
                    elif ext == '.png':
                        image_format = MP4Cover.FORMAT_PNG
                    else:
                        raise MetadataError(f"Unsupported image format: {ext}")

                    self.audio.tags['covr'] = [MP4Cover(image_data, imageformat=image_format)]
                except IOError as e:
                    raise MetadataError(f"Failed to read cover art file: {str(e)}")
            else:
                # Convert value to appropriate type
                if isinstance(value, (bool, int, float)):
                    value = str(value)
                elif not isinstance(value, str):
                    raise ValueError(f"Invalid value type for AAC metadata: {type(value)}")

                try:
                    self.audio.tags[key] = value
                except Exception as e:
                    raise MetadataError(f"Failed to set AAC tag '{key}': {str(e)}")

        except Exception as e:
            raise MetadataError(f"Failed to update AAC metadata '{key}': {str(e)}")

    def update_metadata_from_json(self, json_file: str):
        """
        Update metadata from a JSON file.

        :param json_file: Path to the JSON file containing metadata.
        :raises MetadataError: If JSON is invalid
        :raises ValueError: If metadata structure is invalid
        """
        try:
            with open(json_file, 'r') as f:
                metadata = json.load(f)
        except json.JSONDecodeError as e:
            raise MetadataError(f"Invalid JSON format: {str(e)}")

        if not isinstance(metadata, list):
            raise ValueError("Metadata must contain a list of tag updates")

        for item in metadata:
            if not isinstance(item, dict) or 'tag_key' not in item or 'value' not in item:
                raise ValueError("Each metadata item must have 'tag_key' and 'value' fields")

        self.update_metadata_list([(item['tag_key'], item['value']) for item in metadata])

    def get_metadata_diff(self, original_tags: Dict[str, Any], updated_tags: Dict[str, Any]) -> str:
        """
        Get the difference between original and updated tags.

        :param original_tags: The original tags.
        :param updated_tags: The updated tags.
        :return: A string representation of the differences.
        """
        diff = DeepDiff(
            original_tags,
            updated_tags, 
            ignore_order=True, 
            ignore_string_case=True, 
            verbose_level=2,
            cutoff_intersection_for_pairs=0.8,
            exclude_paths=["root['APIC:Cover']"]
        )
        return diff.pretty()

    def get_current_tags(self) -> Dict[str, Any]:
        """
        Get the current tags of the audio file.

        :return: A dictionary containing the current tags.
        """
        return {tag: self.audio[tag] for tag in self.audio.keys()}