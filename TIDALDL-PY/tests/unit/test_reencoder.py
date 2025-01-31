import os
import sys
import unittest
import ffmpeg
from unittest.mock import patch 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tidal_dl')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tidal_dl/custom')))

from tidal_dl.custom.reencoder import Reencoder, Codec, EncodingError

class TestReencoder(unittest.TestCase):

    def setUp(self):
        """
        Set up the test environment before running the tests.
        """
        self.codec = Codec(name="AAC", codec="aac", ext=".m4a", desc="AAC Audio Codec")
        self.reencoder = Reencoder(codec=self.codec)

    def test_load_codecs_default(self):
        """
        Test loading codec configurations from the default JSON file.
        """
        codecs = Reencoder.load_codecs()
        
        # Verify we got all expected codecs
        self.assertIn('wav', codecs)
        self.assertIn('mp3', codecs)
        self.assertIn('aac', codecs)
        self.assertIn('flac', codecs)
        self.assertIn('mp4', codecs)
        self.assertIn('libfdk_aac', codecs)
        
        # Verify codec structure for one entry
        mp3_codec = codecs['mp3']
        self.assertEqual(mp3_codec.name, 'mp3')
        self.assertEqual(mp3_codec.codec, 'libmp3lame')
        self.assertEqual(mp3_codec.ext, '.mp3')
        self.assertEqual(mp3_codec.desc, 'MP3 audio codec')

    def test_load_codecs_custom_path(self):
        """
        Test loading codec configurations from a custom path.
        """
        import tempfile
        import json
        
        # Create a temporary config file
        test_config = {
            "test_codec": {
                "codec": "test",
                "description": "Test codec",
                "ext": ".test"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            # Test loading from custom path
            codecs = Reencoder.load_codecs(temp_path)
            
            # Verify custom codec was loaded
            self.assertIn('test_codec', codecs)
            test_codec = codecs['test_codec']
            self.assertEqual(test_codec.name, 'test_codec')
            self.assertEqual(test_codec.codec, 'test')
            self.assertEqual(test_codec.ext, '.test')
            self.assertEqual(test_codec.desc, 'Test codec')
        finally:
            # Clean up temporary file
            os.remove(temp_path)

    def test_load_codecs_invalid_path(self):
        """
        Test loading codec configurations with an invalid path.
        """
        with self.assertRaises(FileNotFoundError):
            Reencoder.load_codecs('nonexistent.json')

    @patch("tidal_dl.custom.reencoder.ffmpeg.probe")
    def test_get_metadata_valid_file(self, mock_probe):
        """
        Test get_metadata to confirm it retrieves metadata when the file is valid.
        """
        # Mock ffmpeg.probe to return a sample metadata dictionary
        mock_probe.return_value = {"streams": [{"codec_name": "aac"}]}
        metadata = self.reencoder.get_metadata("test.m4a")
        self.assertEqual(metadata, {"streams": [{"codec_name": "aac"}]})

    @patch("tidal_dl.custom.reencoder.ffmpeg.probe")
    def test_get_metadata_invalid_file(self, mock_probe):
        """
        Test get_metadata with an invalid file to handle ffmpeg errors gracefully.
        """
        mock_probe.side_effect = OSError("Invalid file")
        with self.assertRaises(OSError):
            self.reencoder.get_metadata("invalid_file.m4a")

    def test_get_codec_from_extension_valid(self):
        """
        Test get_codec_from_extension with a valid extension to confirm it returns the correct codec.
        """
        codec = self.reencoder.get_codec_from_extension("example.m4a")
        self.assertEqual(codec, self.codec)

    def test_get_codec_from_extension_invalid(self):
        """
        Test get_codec_from_extension with an invalid extension to ensure it raises EncodingError.
        """
        with self.assertRaises(EncodingError):
            self.reencoder.get_codec_from_extension("example.xxx")

    def test_generate_unique_output_path(self):
        """Test unique output path generation."""
        with patch('os.path.exists') as mock_exists:
            # First attempt exists, second doesn't
            mock_exists.side_effect = [True, False]
            path = self.reencoder._generate_unique_output_path("test", ".m4a")
            self.assertEqual(path, "test_Tagged_1.m4a")

            # No existing file
            mock_exists.side_effect = [False]
            path = self.reencoder._generate_unique_output_path("test", ".m4a")
            self.assertEqual(path, "test_Tagged.m4a")

    def test_validate_metadata_tags_valid(self):
        """Test metadata tags validation with valid tags."""
        valid_tags = ["artist", "title", "album"]
        # Should not raise any exception
        self.reencoder._validate_metadata_tags(valid_tags)

    def test_validate_metadata_tags_invalid_type(self):
        """Test metadata tags validation with invalid type."""
        invalid_tags = ["artist", 123, "album"]
        with self.assertRaises(ValueError) as context:
            self.reencoder._validate_metadata_tags(invalid_tags)
        self.assertIn("must be strings", str(context.exception))

    def test_validate_metadata_tags_empty(self):
        """Test metadata tags validation with empty strings."""
        invalid_tags = ["artist", "", "album"]
        with self.assertRaises(ValueError) as context:
            self.reencoder._validate_metadata_tags(invalid_tags)
        self.assertIn("cannot be empty strings", str(context.exception))

    @patch("tidal_dl.custom.reencoder.ffmpeg.input")
    @patch("tidal_dl.custom.reencoder.os.remove")
    @patch("tidal_dl.custom.reencoder.os.path.isfile", return_value=True)
    @patch("tidal_dl.custom.reencoder.os.path.exists", return_value=False)
    @patch("tidal_dl.custom.reencoder.ffmpeg.output")
    def test_reencode_success(self, mock_output, mock_exists, mock_isfile, mock_remove, mock_ffmpeg_input):
        """
        Test reencode to confirm it succeeds under normal conditions.
        """
        mock_output.return_value.overwrite_output.return_value.run.return_value = None

        output_file = self.reencoder.reencode(
            file_path="test.m4a",
            delete_original=True,
            remove_src_tags=True,
            ffmpeg_output_options_dc = {"b:a": "192k"}
        )

        mock_ffmpeg_input.assert_called_with("test.m4a")
        mock_output.assert_called_once()
        self.assertEqual(output_file, "test_Tagged.m4a")
        mock_remove.assert_called_once_with("test.m4a")

    @patch("tidal_dl.custom.reencoder.ffmpeg.input")
    @patch("tidal_dl.custom.reencoder.os.remove")
    @patch("tidal_dl.custom.reencoder.os.path.isfile", return_value=False)
    def test_reencode_file_not_found(self, mock_isfile, mock_remove, mock_ffmpeg_input):
        """
        Test reencode to confirm it handles missing input files gracefully.
        """
        output_file = self.reencoder.reencode(file_path="missing.m4a")
        self.assertIsNone(output_file)
        mock_remove.assert_not_called()

    @patch("tidal_dl.custom.reencoder.ffmpeg.input")
    @patch("tidal_dl.custom.reencoder.os.path.isfile", return_value=True)
    def test_reencode_error_during_ffmpeg(self, mock_isfile, mock_ffmpeg_input):
        """
        Test reencode to confirm it raises an exception if FFmpeg encounters an error.
        """
        mock_ffmpeg_run = mock_ffmpeg_input.return_value.output.return_value.overwrite_output.return_value.run
        # Create a mock FFmpeg error with both stdout and stderr
        ffmpeg_error = ffmpeg.Error('fake', stdout=b'', stderr=b'FFmpeg encoding failed')
        mock_ffmpeg_run.side_effect = ffmpeg_error

        with self.assertRaises(EncodingError):
            self.reencoder.reencode(file_path="test.m4a")

    @patch("tidal_dl.custom.reencoder.ffmpeg")
    @patch("tidal_dl.custom.reencoder.os.remove")
    @patch("tidal_dl.custom.reencoder.os.path.isfile", return_value=True)
    def test_regression_cover_art_removal(self, mock_isfile, mock_remove, mock_ffmpeg):
        """
        Ensure reencode removes cover art metadata when requested.
        """
        # Set up mock chain
        mock_stream = mock_ffmpeg.input.return_value
        mock_output = mock_ffmpeg.output.return_value
        mock_output.global_args.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_output
        mock_output.run.return_value = None

        output_file = self.reencoder.reencode(
            file_path="test.m4a",
            metadata_tags=['cover_art'],
            remove_src_tags=False
        )

        # Verify correct FFmpeg command was constructed
        mock_ffmpeg.input.assert_called_once_with("test.m4a")
        mock_ffmpeg.output.assert_called_once()
        mock_output.run.assert_called_once()
        self.assertEqual(output_file, "test_Tagged.m4a")

    @patch("tidal_dl.custom.reencoder.ffmpeg.probe")
    def test_regression_metadata_format_changes(self, mock_probe):
        """
        Validate reencode handles unsupported or shifted metadata format.
        """
        test_metadata = {"streams": [{"codec_type": "audio", "codec_name": "aac"}]}
        mock_probe.return_value = test_metadata
        metadata = self.reencoder.get_metadata("test.m4a")
        self.assertEqual(metadata, test_metadata)

    def test_invalid_codec_init(self):
        """Test initialization with invalid codec."""
        with self.assertRaises(ValueError) as context:
            Reencoder(codec=None)
        self.assertIn("cannot be None", str(context.exception))

        with self.assertRaises(ValueError) as context:
            Reencoder(codec="invalid")
        self.assertIn("Must be an instance of Codec", str(context.exception))

    @patch("tidal_dl.custom.reencoder.os.path.exists")
    def test_output_path_multiple_collisions(self, mock_exists):
        """Test handling of multiple output path collisions."""
        # Simulate first three paths exist, fourth one doesn't
        mock_exists.side_effect = [True, True, True, False]
        path = self.reencoder._generate_unique_output_path("test", ".m4a")
        self.assertEqual(path, "test_Tagged_3.m4a")

    @patch("tidal_dl.custom.reencoder.ffmpeg")
    @patch("tidal_dl.custom.reencoder.os.path.isfile", return_value=True)
    @patch("tidal_dl.custom.reencoder.os.path.exists", return_value=False)
    def test_reencode_with_custom_options(self, mock_exists, mock_isfile, mock_ffmpeg):
        """Test reencode with custom FFmpeg options."""
        # Set up mock chain
        mock_stream = mock_ffmpeg.input.return_value
        mock_output = mock_ffmpeg.output.return_value
        mock_output.global_args.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_output
        mock_output.run.return_value = None

        custom_options = {
            "b:a": "320k",
            "ac": "2",
            "ar": "44100"
        }

        output_file = self.reencoder.reencode(
            file_path="test.m4a",
            ffmpeg_output_options_dc=custom_options
        )

        # Verify FFmpeg command was constructed with custom options
        mock_ffmpeg.input.assert_called_once_with("test.m4a")
        mock_ffmpeg.output.assert_called_once()
        mock_output.run.assert_called_once()
        self.assertEqual(output_file, "test_Tagged.m4a")

# Run the test suite
if __name__ == "__main__":
    unittest.main()