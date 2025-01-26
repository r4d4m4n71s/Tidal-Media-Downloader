import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from mutagen import MutagenError

# Adjust the path to include the directory containing the logger_config module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../tidal_dl/custom')))
from tagger import AudioTagger
from audio_codifier import AudioCodec

class TestAudioTagger(unittest.TestCase):

    @patch('tagger.AudioCodifier')
    @patch('tagger.logger')
    def setUp(self, mock_logger, MockAudioCodifier):
        self.mock_audio_codifier = MockAudioCodifier.return_value
        self.mock_audio_codifier.get_codec_from_extension.return_value = AudioCodec.mp3
        self.mock_audio_codifier.reencode_audio.return_value = 'test_file.mp3'
        self.mock_logger = mock_logger
        self.audio_tagger = AudioTagger('test_file.mp3')

    @patch('tagger.MP3')
    @patch('tagger.logger')
    def test_try_get_metadata_from_file_success(self, mock_logger, MockMP3):
        mock_audio = MagicMock()
        MockMP3.return_value = mock_audio
        audio = self.audio_tagger._try_get_metadata_from_file()
        self.assertEqual(audio, mock_audio)
        mock_logger.info.assert_called_with('Loading metadata for: test_file.mp3')

    @patch('tagger.MP3')
    @patch('tagger.logger')
    def test_try_get_metadata_from_file_failure(self, mock_logger, MockMP3):
        MockMP3.side_effect = MutagenError('Test exception')
        self.mock_audio_codifier.reencode_audio.return_value = 'reencoded_file_path.mp3'
        with patch('tagger.AudioTagger._get_audio_file', side_effect=[MutagenError('Test exception'), MagicMock()]):
            audio = self.audio_tagger._try_get_metadata_from_file()
            self.assertIsNotNone(audio)
            mock_logger.error.assert_called()

    @patch('tagger.MP3')
    @patch('tagger.logger')
    def test_tag_track_mp3(self, mock_logger, MockMP3):
        mock_audio = MagicMock()
        MockMP3.return_value = mock_audio
        metadata = {
            'title': 'Test Title',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'tracknumber': '1',
            'date': '2023',
            'genre': 'Test Genre',
            'copyright': 'Test Copyright',
            'discnumber': '1',
            'composer': 'Test Composer',
            'isrc': 'Test ISRC',
            'albumartist': 'Test Album Artist',
            'totaldisc': '1',
            'lyrics': 'Test Lyrics'
        }
        self.audio_tagger.tag_track(metadata)
        mock_audio.save.assert_called_once()
        mock_logger.info.assert_called_with('Successfully tagged test_file.mp3 (MP3) with metadata: {}'.format(metadata.get("title", "")))

    @patch('tagger.MP3')
    @patch('tagger.logger')
    def test_tag_track_mp3_with_cover_art(self, mock_logger, MockMP3):
        mock_audio = MagicMock()
        MockMP3.return_value = mock_audio
        metadata = {
            'title': 'Test Title',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'tracknumber': '1',
            'date': '2023',
            'genre': 'Test Genre',
            'copyright': 'Test Copyright',
            'discnumber': '1',
            'composer': 'Test Composer',
            'isrc': 'Test ISRC',
            'albumartist': 'Test Album Artist',
            'totaldisc': '1',
            'lyrics': 'Test Lyrics'
        }
        cover_art_path = 'test_cover.jpg'
        with patch('builtins.open', unittest.mock.mock_open(read_data=b'test_data')):
            with patch('tagger.AudioTagger._get_audio_file', return_value=mock_audio):
                self.audio_tagger = AudioTagger('test_file.mp3')
                self.audio_tagger.tag_track(metadata, cover_art_path)
                mock_audio.save.assert_called_once()
                mock_logger.info.assert_called_with('Successfully tagged test_file.mp3 (MP3) with metadata: {}'.format(metadata.get("title", "")))

if __name__ == '__main__':
    unittest.main()
