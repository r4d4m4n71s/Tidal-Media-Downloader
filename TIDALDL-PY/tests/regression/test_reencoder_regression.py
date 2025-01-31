import unittest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tidal_dl')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tidal_dl/custom')))

from tidal_dl.custom.reencoder import Reencoder, Codec

class TestReencoderRegression(unittest.TestCase):

    def setUp(self):
        """
        Set up testing dependencies.
        """
        # Load all available codecs
        self.codecs = Reencoder.load_codecs()
        
        # Set up paths
        self.resources_dir = os.path.join(os.path.dirname(__file__), '../resources')
        self.output_dir = os.path.normpath( os.path.join(os.getcwd(), "tests/output/"))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize reencoder with FLAC codec for testing
        self.reencoder = Reencoder(codec=self.codecs['flac'])
        
        # Source files for tests (both with and without tags)
        self.audio_dir = os.path.join(self.resources_dir, 'audio')
        self.source_files = {
            'wav': {
                'tagged': os.path.join(self.audio_dir, 'test.wav'),
                'untagged': os.path.join(self.audio_dir, 'test_notags.wav')
            },
            'flac': {
                'tagged': os.path.join(self.audio_dir, 'test.flac'),
                'untagged': os.path.join(self.audio_dir, 'test_notags.flac')
            },
            'mp3': {
                'tagged': os.path.join(self.audio_dir, 'test.mp3'),
                'untagged': os.path.join(self.audio_dir, 'test_notags.mp3')
            },
            'mp4': {
                'tagged': os.path.join(self.audio_dir, 'test.m4a'),
                'untagged': os.path.join(self.audio_dir, 'test_notags.m4a')
            }
        }
        
        # Expected metadata for verification
        self.expected_metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'lyrics': 'Test lyrics\nSecond line',
            'album':''
        }
        
        # Verify test files exist
        for fmt_files in self.source_files.values():
            for path in fmt_files.values():
                self.assertTrue(os.path.exists(path), f"Test file {path} not found")

    def tearDown(self):
        """
        Clean up test output files.
        """
        if os.path.exists(self.output_dir):
            for file_name in os.listdir(self.output_dir):
                file_path = os.path.join(self.output_dir, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    def test_format_conversions_with_metadata(self):
        """Test converting between different audio formats while preserving metadata"""
        source_formats = ['flac', 'mp4', 'mp3']
        target_formats = ['wav', 'flac', 'mp3', 'mp4']
        
        for src_fmt in source_formats:
            for tgt_fmt in target_formats:
                with self.subTest(source=src_fmt, target=tgt_fmt):
                    output_path = os.path.join(self.output_dir, f"output.{tgt_fmt}")
                    # Prepare metadata options - use proper FFmpeg metadata format                    
                    result = self.reencoder.reencode(
                        file_path=self.source_files[src_fmt]['tagged'],
                        output_path=output_path,
                        codec=self.codecs[tgt_fmt],
                        metadata_tags= [f"{key}={value}" for key, value in self.expected_metadata.items()]
                    )
                    self.assertTrue(os.path.isfile(result))
                    self.assertTrue(result.endswith(f".{tgt_fmt}"))
                    
                    # Verify metadata was preserved (except for WAV which doesn't support all tags)
                    if tgt_fmt != 'wav':
                        metadata = self.reencoder.get_metadata(result)
                        tags = metadata.get('format', {}).get('tags', {})
                        for key, value in self.expected_metadata.items():
                            self.assertEqual(tags.get(key), value)

    def test_format_conversions_without_metadata(self):
        """Test converting between different audio formats with untagged files"""
        source_formats = ['flac', 'mp4', 'mp3']
        target_formats = ['wav', 'flac', 'mp3', 'mp4']
        
        for src_fmt in source_formats:
            for tgt_fmt in target_formats:
                with self.subTest(source=src_fmt, target=tgt_fmt):
                    output_path = os.path.join(self.output_dir, f"output.{tgt_fmt}")
                    result = self.reencoder.reencode(
                        file_path=self.source_files[src_fmt]['untagged'],
                        output_path=output_path,
                        codec=self.codecs[tgt_fmt],
                        remove_src_tags=True,  # Ensure no tags are present
                        ffmpeg_global_options_ls={'map': '0:a'}  # Only map audio stream
                    )
                    self.assertTrue(os.path.isfile(result))
                    self.assertTrue(result.endswith(f".{tgt_fmt}"))
                    
                    # Verify no user metadata tags are present
                    metadata = self.reencoder.get_metadata(result)
                    tags = metadata.get('format', {}).get('tags', {})
                    # FFmpeg may add encoder-related tags, so we only check for absence of our metadata
                    for key in self.expected_metadata.keys():
                        self.assertNotIn(key, tags, f"Found unexpected metadata tag: {key}")

    def test_adding_metadata_to_untagged(self):
        """Test adding metadata to untagged files during conversion"""
        test_metadata = {
            'title': 'New Title',
            'artist': 'New Artist',
            'lyrics': 'New Lyrics'
        }
        
        for fmt in ['flac', 'mp3', 'mp4']:
            with self.subTest(format=fmt):
                output_path = os.path.join(self.output_dir, f"output.{fmt}")
                ffmpeg_options = {
                    'map': '0:a',  # Only map audio stream
                    **{f'metadata:{key}': value for key, value in test_metadata.items()}
                }
                result = self.reencoder.reencode(
                    file_path=self.source_files[fmt]['untagged'],
                    output_path=output_path,
                    codec=self.codecs[fmt],
                    ffmpeg_global_options_ls=ffmpeg_options
                )
                
                metadata = self.reencoder.get_metadata(result)
                tags = metadata.get('format', {}).get('tags', {})
                for key, value in test_metadata.items():
                    self.assertEqual(tags.get(key), value)

    def test_metadata_removal_from_tagged(self):
        """Test removing all metadata from tagged files"""
        for fmt in ['flac', 'mp3', 'mp4']:
            with self.subTest(format=fmt):
                output_path = os.path.join(self.output_dir, f"output_no_tags.{fmt}")
                result = self.reencoder.reencode(
                    file_path=self.source_files[fmt]['tagged'],
                    output_path=output_path,
                    codec=self.codecs[fmt],
                    remove_src_tags=True,
                    ffmpeg_global_options_ls={'map': '0:a'}  # Only map audio stream
                )
                
                metadata = self.reencoder.get_metadata(result)
                tags = metadata.get('format', {}).get('tags', {})
                # FFmpeg may add encoder-related tags, so we only check for absence of our metadata
                for key in self.expected_metadata.keys():
                    self.assertNotIn(key, tags, f"Found unexpected metadata tag: {key}")

    def test_specific_tag_removal(self):
        """Test removing specific metadata tags"""
        for fmt in ['flac', 'mp3', 'mp4']:
            with self.subTest(format=fmt):
                output_path = os.path.join(self.output_dir, f"output_no_title.{fmt}")
                # Use ffmpeg_options to preserve specific tags while removing others
                ffmpeg_options = {
                    'map': '0:a',  # Only map audio stream
                    'metadata:title': '',  # Remove title
                    'metadata:artist': self.expected_metadata['artist'],  # Keep artist
                    'metadata:lyrics': self.expected_metadata['lyrics']   # Keep lyrics
                }
                result = self.reencoder.reencode(
                    file_path=self.source_files[fmt]['tagged'],
                    output_path=output_path,
                    codec=self.codecs[fmt],
                    ffmpeg_global_options_ls=ffmpeg_options
                )
                
                metadata = self.reencoder.get_metadata(result)
                tags = metadata.get('format', {}).get('tags', {})
                
                # Verify title is removed
                self.assertNotIn('title', tags)
                
                # Verify other tags are preserved
                self.assertEqual(tags.get('artist'), self.expected_metadata['artist'])
                self.assertEqual(tags.get('lyrics'), self.expected_metadata['lyrics'])
                # Verify correct output format
                self.assertTrue(result.endswith(f".{fmt}"))
    

if __name__ == "__main__":
    unittest.main()