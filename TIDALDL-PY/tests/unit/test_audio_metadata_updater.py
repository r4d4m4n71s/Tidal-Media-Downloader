import unittest
import os
import sys
from unittest.mock import patch, mock_open, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tidal_dl')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tidal_dl/custom')))


from tidal_dl.custom.custom_mapper import (
    AudioMetadataUpdater,
    MetadataError,
    AudioFormatError
)
from mutagen.id3 import ID3
from mutagen.flac import Picture

class TestAudioMetadataUpdater(unittest.TestCase):

    def setUp(self):
        print("Starting setUp")
        self.resources_dir = os.path.join(
            os.path.dirname(__file__), '..', 'resources', 'audio')
        print(f"Resources dir: {self.resources_dir}")
        self.tags_path = os.path.join(os.path.dirname(__file__), '..', '..', 'tidal_dl', 'custom', '_config', 'tags.json')
        print(f"Tags path: {self.tags_path}")
        print("Checking if paths exist:")
        print(f"Resources dir exists: {os.path.exists(self.resources_dir)}")
        print(f"Tags path exists: {os.path.exists(self.tags_path)}")

    @patch('tidal_dl.custom.custom_mapper.FLAC')
    @patch('tidal_dl.custom.custom_mapper.MP3')
    @patch('tidal_dl.custom.custom_mapper.MP4')
    @patch('tidal_dl.custom.custom_mapper.WAVE')
    @patch('tidal_dl.custom.custom_mapper.AAC')
    @patch('tidal_dl.custom.custom_mapper.os.path.exists', return_value=True)
    def test_load_audio_file(self, mock_exists, mock_aac, mock_wave, mock_mp4, mock_mp3, mock_flac):
        # Setup mock returns
        mock_mp3_instance = MagicMock()
        mock_mp3_instance.tags = None
        mock_mp3.return_value = mock_mp3_instance

        mock_aac_instance = MagicMock()
        mock_aac_instance.tags = None
        mock_aac.return_value = mock_aac_instance

        # Test FLAC
        test_flac_path = os.path.join(self.resources_dir, 'test.flac')
        updater = AudioMetadataUpdater(test_flac_path, self.tags_path)
        audio = updater._load_audio_file()
        mock_flac.assert_called_once_with(test_flac_path)

        # Test MP3
        test_mp3_path = os.path.join(self.resources_dir, 'test.mp3')
        updater = AudioMetadataUpdater(test_mp3_path, self.tags_path)
        audio = updater._load_audio_file()
        mock_mp3.assert_called_once_with(test_mp3_path, ID3=ID3)
        #self.assertIsNotNone(audio.tags)  # Verify tags were initialized

        # Test MP4
        test_mp4_path = os.path.join(self.resources_dir, 'test.mp4')
        updater = AudioMetadataUpdater(test_mp4_path, self.tags_path)
        audio = updater._load_audio_file()
        mock_mp4.assert_called_once_with(test_mp4_path)

        # Test WAV
        test_wav_path = os.path.join(self.resources_dir, 'test.wav')
        updater = AudioMetadataUpdater(test_wav_path, self.tags_path)
        audio = updater._load_audio_file()
        mock_wave.assert_called_once_with(test_wav_path)

        # Test AAC
        test_aac_path = os.path.join(self.resources_dir, 'test.aac')
        updater = AudioMetadataUpdater(test_aac_path, self.tags_path)
        audio = updater._load_audio_file()
        mock_aac.assert_called_once_with(test_aac_path)
        #self.assertIsNotNone(audio.tags)  # Verify tags were initialized

        # Test unsupported format
        test_xyz_path = os.path.join(self.resources_dir, 'test.xyz')
        updater = AudioMetadataUpdater(test_xyz_path, self.tags_path)
        with self.assertRaises(AudioFormatError) as context:
            updater._load_audio_file()
        self.assertIn("Unsupported audio format", str(context.exception))

    @patch('builtins.open')
    def test_load_tag_mappings(self, mock_open):
        # Mock the tags file with valid JSON data
        mock_open.return_value.__enter__.return_value.read.return_value = '''
        {
            "mp3_tags": {
                "title": {"mutagen_frame": "TIT2"},
                "artist": {"mutagen_frame": "TPE1"}
            },
            "mp4_tags": {
                "title": {"mutagen_key": "©nam"},
                "artist": {"mutagen_key": "©ART"}
            }
        }
        '''
        updater = AudioMetadataUpdater(os.path.join(self.resources_dir, 'test.mp3'), self.tags_path)
        mp3_tags, mp4_tags = updater._load_tag_mappings(self.tags_path)
        self.assertEqual(len(mp3_tags), 2)
        self.assertEqual(len(mp4_tags), 2)
        self.assertEqual(mp3_tags['title']['mutagen_frame'], 'TIT2')
        self.assertEqual(mp4_tags['title']['mutagen_key'], '©nam')

    @patch('tidal_dl.custom.custom_mapper.FLAC')
    @patch('tidal_dl.custom.custom_mapper.os.path.exists', return_value=True)
    def test_update_metadata_list(self, mock_exists, mock_flac):
        # Setup mock
        mock_audio = MagicMock()
        mock_flac.return_value = mock_audio
        mock_audio.tags = None
        
        test_flac_path = os.path.join(self.resources_dir, 'test.flac')
        updater = AudioMetadataUpdater(test_flac_path, self.tags_path)
        
        # Test with valid metadata
        updater.update_metadata_list([('title', 'Test Title')])
        mock_audio.__setitem__.assert_called_with('title', 'Test Title')
        mock_audio.save.assert_called_once()
        
        # Test with invalid encoding
        with self.assertRaises(ValueError) as context:
            updater.update_metadata_list([('title', 'Test')], encoding=0)
        self.assertIn("Encoding must be", str(context.exception))
        
        # Test with invalid language
        with self.assertRaises(ValueError) as context:
            updater.update_metadata_list([('title', 'Test')], lang='en')
        self.assertIn("Language code must be", str(context.exception))

    @patch('tidal_dl.custom.custom_mapper.FLAC')
    @patch('tidal_dl.custom.custom_mapper.os.path.exists', return_value=True)
    def test_update_or_add_metadata(self, mock_exists, mock_flac):
        # Setup mock
        mock_audio = MagicMock()
        mock_flac.return_value = mock_audio
        mock_audio.tags = None
        
        test_flac_path = os.path.join(self.resources_dir, 'test.flac')
        updater = AudioMetadataUpdater(test_flac_path, self.tags_path)
        
        # Test basic metadata update
        updater.update_or_add_metadata('title', 'Test Title')
        mock_audio.__setitem__.assert_called_with('title', 'Test Title')
        mock_audio.save.assert_called()
        
        # Test with invalid encoding
        with self.assertRaises(ValueError) as context:
            updater.update_or_add_metadata('title', 'Test', encoding=0)
        self.assertIn("Encoding must be", str(context.exception))
        
        # Test with invalid language
        with self.assertRaises(ValueError) as context:
            updater.update_or_add_metadata('title', 'Test', lang='en')
        self.assertIn("Language code must be", str(context.exception))

    def test_invalid_metadata_key(self):
        """Test handling of invalid metadata keys."""
        test_flac_path = os.path.join(self.resources_dir, 'test.flac')
        updater = AudioMetadataUpdater(test_flac_path, self.tags_path)
        with self.assertRaises(ValueError) as context:
            updater.update_or_add_metadata('', 'Test Value')
        self.assertIn("must be a non-empty string", str(context.exception))

        with self.assertRaises(ValueError) as context:
            updater.update_or_add_metadata(None, 'Test Value')
        self.assertIn("must be a non-empty string", str(context.exception))

    @patch('tidal_dl.custom.custom_mapper.FLAC')
    @patch('tidal_dl.custom.custom_mapper.os.path.exists', return_value=True)
    def test_value_type_conversion(self, mock_exists, mock_flac):
        """Test value type conversion for different metadata types."""
        mock_audio = MagicMock()
        mock_flac.return_value = mock_audio
        test_flac_path = os.path.join(self.resources_dir, 'test.flac')
        updater = AudioMetadataUpdater(test_flac_path, self.tags_path)

        # Test boolean conversion
        updater.update_or_add_metadata('test_bool', True)
        mock_audio.__setitem__.assert_called_with('test_bool', 'True')

        # Test integer conversion
        updater.update_or_add_metadata('test_int', 123)
        mock_audio.__setitem__.assert_called_with('test_int', '123')

        # Test float conversion
        updater.update_or_add_metadata('test_float', 123.45)
        mock_audio.__setitem__.assert_called_with('test_float', '123.45')

        # Test invalid type
        with self.assertRaises(ValueError) as context:
            updater.update_or_add_metadata('test_invalid', {'key': 'value'})
        self.assertIn("Invalid value type", str(context.exception))

    @patch('tidal_dl.custom.custom_mapper.os.path.exists')
    @patch('tidal_dl.custom.custom_mapper.FLAC')
    def test_cover_art_validation(self, mock_flac, mock_exists):
        """Test cover art file validation."""
        mock_audio = MagicMock()
        mock_flac.return_value = mock_audio
        
        test_flac_path = os.path.join(self.resources_dir, 'test.flac')
        updater = AudioMetadataUpdater(test_flac_path, self.tags_path)
        
        # Test missing cover art file
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError) as context:
            updater.update_or_add_metadata('cover_art', 'nonexistent.jpg')
        self.assertIn("Cover art file not found", str(context.exception))

        # Test unsupported image format
        mock_exists.return_value = True
        
        with patch('builtins.open', mock_open()):
            with self.assertRaises(MetadataError) as context:
                updater.update_or_add_metadata('cover_art', 'image.bmp')
            self.assertIn("Unsupported image format: .bmp", str(context.exception))

    @patch('tidal_dl.custom.custom_mapper.FLAC')
    @patch('tidal_dl.custom.custom_mapper.os.path.exists', return_value=True)
    def test_update_metadata_from_json(self, mock_exists, mock_flac):
        """Test JSON metadata update validation."""
        mock_audio = MagicMock()
        mock_flac.return_value = mock_audio
        test_flac_path = os.path.join(self.resources_dir, 'test.flac')
        
        # Valid tags file content
        tags_json = '''{
            "mp3_tags": {"title": {"mutagen_frame": "TIT2"}},
            "mp4_tags": {"title": {"mutagen_key": "©nam"}}
        }'''
        
        test_cases = [
            {
                'name': 'invalid_json',
                'content': 'invalid json',
                'error_type': MetadataError,
                'error_msg': "Invalid JSON format"
            },
            {
                'name': 'invalid_structure',
                'content': '{"invalid": "structure"}',
                'error_type': ValueError,
                'error_msg': "must contain a list"
            },
            {
                'name': 'missing_fields',
                'content': '[{"missing_fields": true}]',
                'error_type': ValueError,
                'error_msg': "must have 'tag_key' and 'value' fields"
            },
            {
                'name': 'valid_metadata',
                'content': '[{"tag_key": "title", "value": "Test Song"}]',
                'error_type': None,
                'error_msg': None
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(name=test_case['name']):
                mock_file = mock_open(read_data=tags_json)
                mock_metadata_file = mock_open(read_data=test_case['content'])
                mock_file.side_effect = [mock_file.return_value, mock_metadata_file.return_value]
                
                with patch('builtins.open', mock_file):
                    updater = AudioMetadataUpdater(test_flac_path, self.tags_path)
                    if test_case['error_type']:
                        with self.assertRaises(test_case['error_type']) as context:
                            updater.update_metadata_from_json(os.path.join(self.resources_dir, 'metadata.json'))
                        self.assertIn(test_case['error_msg'], str(context.exception))
                    else:
                        updater.update_metadata_from_json(os.path.join(self.resources_dir, 'metadata.json'))
                        mock_audio.__setitem__.assert_called_with('title', 'Test Song')

    def test_invalid_encoding_parameter(self):
        """Test validation of encoding parameter."""
        test_mp3_path = os.path.join(self.resources_dir, 'test.mp3')
        updater = AudioMetadataUpdater(test_mp3_path, self.tags_path)
        
        with self.assertRaises(ValueError) as context:
            updater.update_metadata_list([('title', 'Test')], encoding=0)
        self.assertIn("Encoding must be between 1 and 4", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            updater.update_metadata_list([('title', 'Test')], encoding=5)
        self.assertIn("Encoding must be between 1 and 4", str(context.exception))

    def test_invalid_language_parameter(self):
        """Test validation of language parameter."""
        test_mp3_path = os.path.join(self.resources_dir, 'test.mp3')
        updater = AudioMetadataUpdater(test_mp3_path, self.tags_path)
        
        with self.assertRaises(ValueError) as context:
            updater.update_metadata_list([('title', 'Test')], lang='en')
        self.assertIn("Language code must be a 3-letter ISO 639-2 code", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            updater.update_metadata_list([('title', 'Test')], lang='english')
        self.assertIn("Language code must be a 3-letter ISO 639-2 code", str(context.exception))

    @patch('tidal_dl.custom.custom_mapper.MP3')
    @patch('tidal_dl.custom.custom_mapper.os.path.exists', return_value=True)
    def test_mp3_specific_metadata(self, mock_exists, mock_mp3):
        """Test MP3-specific metadata handling."""
        mock_audio = MagicMock()
        mock_tags = MagicMock()
        mock_audio.tags = mock_tags
        mock_mp3.return_value = mock_audio
        
        test_mp3_path = os.path.join(self.resources_dir, 'test.mp3')
        updater = AudioMetadataUpdater(test_mp3_path, self.tags_path)
        
        # Mock the tag mappings with proper module.class format
        updater._mp3_tag_cache = {'lyrics': {'mutagen_frame': 'mutagen.id3.USLT'}}
        
        # Test lyrics with language
        updater.update_or_add_metadata('lyrics', 'Test lyrics', lang='spa')
        self.assertTrue(mock_tags.add.called)
        
        # Test custom frame
        updater.update_or_add_metadata('custom_tag', 'Custom value')
        self.assertTrue(mock_tags.add.called)

    @patch('tidal_dl.custom.custom_mapper.MP4')
    @patch('tidal_dl.custom.custom_mapper.os.path.exists', return_value=True)
    def test_mp4_specific_metadata(self, mock_exists, mock_mp4):
        """Test MP4-specific metadata handling."""
        mock_audio = MagicMock()
        mock_mp4.return_value = mock_audio
        
        test_mp4_path = os.path.join(self.resources_dir, 'test.m4a')
        updater = AudioMetadataUpdater(test_mp4_path, self.tags_path)
        
        # Test standard MP4 tag
        updater.update_or_add_metadata('title', 'Test Title')
        mock_audio.__setitem__.assert_called()
        
        # Test custom iTunes tag
        updater.update_or_add_metadata('custom_tag', 'Custom value')
        mock_audio.__setitem__.assert_called()

    @patch('tidal_dl.custom.custom_mapper.os.path.exists', return_value=False)
    def test_file_not_found(self, mock_exists):
        """Test file not found handling."""
        test_flac_path = os.path.join(self.resources_dir, 'nonexistent.flac')
        with self.assertRaises(FileNotFoundError) as context:
            AudioMetadataUpdater(test_flac_path, self.tags_path)
        self.assertIn("Audio file not found", str(context.exception))

        mock_exists.side_effect = [True, False]
        test_flac_path = os.path.join(self.resources_dir, 'test.flac')
        with self.assertRaises(FileNotFoundError) as context:
            AudioMetadataUpdater(test_flac_path, os.path.join(self.resources_dir, 'nonexistent.json'))
        self.assertIn("Tags mapping file not found", str(context.exception))

    def test_unsupported_audio_format(self):
        """Test handling of unsupported audio formats."""
        test_path = os.path.join(self.resources_dir, 'test.xyz')
        with patch('tidal_dl.custom.custom_mapper.os.path.exists', return_value=True):
            with self.assertRaises(AudioFormatError) as context:
                updater = AudioMetadataUpdater(test_path, self.tags_path)
                updater._load_audio_file()
            self.assertIn("Unsupported audio format", str(context.exception))

if __name__ == '__main__':
    unittest.main()
