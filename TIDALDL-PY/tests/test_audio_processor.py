import os
import sys
import unittest

# Adjust the path to include the directory containing the logger_config module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../tidal_dl/custom')))
from audio_codifier import AudioCodifier, AudioCodec

class TestAudioProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = AudioCodifier()
        self.file_name = "ok"
        self.test_files_dir = "tests/test_files"
        self.output_dir = "tests/output"
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        for file_name in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

    # def test_reencode_flac_to_flac_methadata_damaged(self):
    #     input_file = os.path.join(self.test_files_dir, f"incomplete_metadata.flac")
    #     output_file = self.processor.reencode_audio(input_file, self.output_dir, AudioCodec.flac)
    #     self.assertTrue(os.path.isfile(output_file))
    #     self.assertTrue(output_file.endswith(".flac"))

    # def test_reencode_flac_to_wav(self):
    #     input_file = os.path.join(self.test_files_dir, f"{self.file_name}.flac")
    #     output_file = self.processor.reencode_audio(input_file, self.output_dir, AudioCodec.wav)
    #     self.assertTrue(os.path.isfile(output_file))
    #     self.assertTrue(output_file.endswith(".wav"))

    # def test_reencode_flac_to_mp3(self):
    #     input_file = os.path.join(self.test_files_dir, f"{self.file_name}.flac")
    #     output_file = self.processor.reencode_audio(input_file, self.output_dir, AudioCodec.mp3)
    #     self.assertTrue(os.path.isfile(output_file))
    #     self.assertTrue(output_file.endswith(".mp3"))

    # def test_reencode_mp3_to_aac(self):
    #     input_file = os.path.join(self.test_files_dir, f"{self.file_name}.mp3")
    #     output_file = self.processor.reencode_audio(input_file, self.output_dir, AudioCodec.aac)
    #     self.assertTrue(os.path.isfile(output_file))
    #     self.assertTrue(output_file.endswith(".m4a"))

    # def test_reencode_wav_to_flac(self):
    #     input_file = os.path.join(self.test_files_dir, f"{self.file_name}.wav")
    #     output_file = self.processor.reencode_audio(input_file, self.output_dir, AudioCodec.flac)
    #     self.assertTrue(os.path.isfile(output_file))
    #     self.assertTrue(output_file.endswith(".flac"))
    
    # def test_reencode_wav_to_mp3(self):
    #     input_file = os.path.join(self.test_files_dir, f"{self.file_name}.wav")
    #     output_file = self.processor.reencode_audio(input_file, self.output_dir, AudioCodec.mp3)
    #     self.assertTrue(os.path.isfile(output_file))
    #     self.assertTrue(output_file.endswith(".mp3"))

    def test_reencode_flac_to_aac(self):
        input_file = os.path.join(self.test_files_dir, f"{self.file_name}.flac")
        output_file = self.processor.reencode_audio(input_file, self.output_dir, AudioCodec.aac)
        self.assertTrue(os.path.isfile(output_file))
        self.assertTrue(output_file.endswith(".aac"))

if __name__ == "__main__":
    unittest.main()
