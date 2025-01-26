import os
import sys
import unittest
import shutil
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE
from mutagen.aiff import AIFF

# Adjust the path to include the directory containing the logger_config module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../tidal_dl/custom')))
from tagger import AudioTagger

class TestAudioTagger(unittest.TestCase):

    def setUp(self):
        self.test_files_dir = "tests/test_files"
        self.output_dir = "tests/output"
        self.cover_art = "cover.jpg"
        os.makedirs(self.output_dir, exist_ok=True)
        self.cover_file = os.path.join(self.test_files_dir, "cover.jpg")
        
        self.metadata = {
            "title": "Test Title",
            "artist": "Test Artist",
            "album": "Test Album",
            "tracknumber": "1",
            "date": "2023",
            "genre": "Test Genre",
            "copyright": "© 2023 Test Records",
            "discnumber": "1",
            "composer": "Test Composer",
            "isrc": "USXYZ1234567",
            "albumartist": "Test Album Artist",
            "totaldisc": "1",
            "lyrics": "Test lyrics.",
        }

    def tearDown(self):
        for file_name in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, file_name)
            #if os.path.isfile(file_path):
                #os.remove(file_path)

    # def test_tag_wav(self):
    #     input_file = os.path.join(self.test_files_dir, "ok.wav")
    #     output_file = os.path.join(self.output_dir, "ok_tagged.wav")
    #     shutil.copy(input_file, output_file)

    #     tagger = AudioTagger(output_file)
    #     tagger.tag_track(self.metadata, self.cover_file)

    #     audio = WAVE(output_file)
    #     self.assertEqual(audio["title"][0], self.metadata["title"])
    #     self.assertEqual(audio["artist"][0], self.metadata["artist"])
    #     self.assertEqual(audio["album"][0], self.metadata["album"])
    #     self.assertEqual(audio["tracknumber"][0], self.metadata["tracknumber"])
    #     self.assertEqual(audio["date"][0], self.metadata["date"])
    #     self.assertEqual(audio["genre"][0], self.metadata["genre"])
    #     self.assertEqual(audio["copyright"][0], self.metadata["copyright"])
    #     self.assertEqual(audio["discnumber"][0], self.metadata["discnumber"])
    #     self.assertEqual(audio["composer"][0], self.metadata["composer"])
    #     self.assertEqual(audio["isrc"][0], self.metadata["isrc"])
    #     self.assertEqual(audio["albumartist"][0], self.metadata["albumartist"])
    #     self.assertEqual(audio["totaldiscs"][0], self.metadata["totaldisc"])
    #     self.assertEqual(audio["lyrics"][0], self.metadata["lyrics"])

    def test_tag_flac(self):
        input_file = os.path.join(self.test_files_dir, "ok.flac")
        output_file = os.path.join(self.output_dir, "ok_tagged.flac")
        
        shutil.copy(input_file, output_file)

        tagger = AudioTagger(output_file)
        tagger.tag_track(self.metadata, self.cover_file)

        audio = FLAC(output_file)
        self.assertEqual(audio["title"][0], self.metadata["title"])
        self.assertEqual(audio["artist"][0], self.metadata["artist"])
        self.assertEqual(audio["album"][0], self.metadata["album"])
        self.assertEqual(audio["tracknumber"][0], self.metadata["tracknumber"])
        self.assertEqual(audio["date"][0], self.metadata["date"])
        self.assertEqual(audio["genre"][0], self.metadata["genre"])
        self.assertEqual(audio["copyright"][0], self.metadata["copyright"])
        self.assertEqual(audio["discnumber"][0], self.metadata["discnumber"])
        self.assertEqual(audio["composer"][0], self.metadata["composer"])
        self.assertEqual(audio["isrc"][0], self.metadata["isrc"])
        self.assertEqual(audio["albumartist"][0], self.metadata["albumartist"])
        self.assertEqual(audio["totaldiscs"][0], self.metadata["totaldisc"])
    #     self.assertEqual(audio["lyrics"][0], self.metadata["lyrics"])

    # def test_tag_mp3(self):
    #     input_file = os.path.join(self.test_files_dir, "ok.mp3")
    #     output_file = os.path.join(self.output_dir, "ok_tagged.mp3")
    #     shutil.copy(input_file, output_file)

    #     tagger = AudioTagger(output_file)
    #     tagger.tag_track(self.metadata, self.cover_file)

    #     audio = MP3(output_file)
    #     self.assertEqual(audio["TIT2"].text[0], self.metadata["title"])
    #     self.assertEqual(audio["TPE1"].text[0], self.metadata["artist"])
    #     self.assertEqual(audio["TALB"].text[0], self.metadata["album"])
    #     self.assertEqual(audio["TRCK"].text[0], self.metadata["tracknumber"])
    #     self.assertEqual(audio["TDRC"].text[0], self.metadata["date"])
    #     self.assertEqual(audio["TCON"].text[0], self.metadata["genre"])
    #     self.assertEqual(audio["TCOP"].text[0], self.metadata["copyright"])
    #     self.assertEqual(audio["TPOS"].text[0], self.metadata["discnumber"])
    #     self.assertEqual(audio["TCOM"].text[0], self.metadata["composer"])
    #     self.assertEqual(audio["TSRC"].text[0], self.metadata["isrc"])
    #     self.assertEqual(audio["TPE2"].text[0], self.metadata["albumartist"])
    #     self.assertEqual(audio["USLT::'eng'"].text, self.metadata["lyrics"])

    # def test_tag_aac(self):
    #     input_file = os.path.join(self.test_files_dir, "ok.m4a")
    #     output_file = os.path.join(self.output_dir, "ok_tagged.m4a")
    #     shutil.copy(input_file, output_file)

    #     tagger = AudioTagger(output_file)
    #     tagger.tag_track(self.metadata, self.cover_file)

    #     audio = MP4(output_file)
    #     self.assertEqual(audio["\xa9nam"][0], self.metadata["title"])
    #     self.assertEqual(audio["\xa9ART"][0], self.metadata["artist"])
    #     self.assertEqual(audio["\xa9alb"][0], self.metadata["album"])
    #     self.assertEqual(audio["trkn"][0][0], int(self.metadata["tracknumber"]))
    #     self.assertEqual(audio["\xa9day"][0], self.metadata["date"])
    #     self.assertEqual(audio["\xa9gen"][0], self.metadata["genre"])
    #     self.assertEqual(audio["cprt"][0], self.metadata["copyright"])
    #     self.assertEqual(audio["disk"][0][0], int(self.metadata["discnumber"]))
    #     self.assertEqual(audio["\xa9wrt"][0], self.metadata["composer"])
    #     self.assertEqual(audio["----:com.apple.iTunes:ISRC"][0].decode("utf-8"), self.metadata["isrc"])
    #     self.assertEqual(audio["aART"][0], self.metadata["albumartist"])
    #     self.assertEqual(audio["\xa9lyr"][0], self.metadata["lyrics"])

    # def test_tag_ogg(self):
    #     input_file = os.path.join(self.test_files_dir, "ok.ogg")
    #     output_file = os.path.join(self.output_dir, "ok_tagged.ogg")
    #     shutil.copy(input_file, output_file)

    #     tagger = AudioTagger(output_file)
    #     tagger.tag_track(self.metadata, self.cover_file)

    #     audio = OggVorbis(output_file)
    #     self.assertEqual(audio["title"][0], self.metadata["title"])
    #     self.assertEqual(audio["artist"][0], self.metadata["artist"])
    #     self.assertEqual(audio["album"][0], self.metadata["album"])
    #     self.assertEqual(audio["tracknumber"][0], self.metadata["tracknumber"])
    #     self.assertEqual(audio["date"][0], self.metadata["date"])
    #     self.assertEqual(audio["genre"][0], self.metadata["genre"])
    #     self.assertEqual(audio["copyright"][0], self.metadata["copyright"])
    #     self.assertEqual(audio["discnumber"][0], self.metadata["discnumber"])
    #     self.assertEqual(audio["composer"][0], self.metadata["composer"])
    #     self.assertEqual(audio["isrc"][0], self.metadata["isrc"])
    #     self.assertEqual(audio["albumartist"][0], self.metadata["albumartist"])
    #     self.assertEqual(audio["totaldiscs"][0], self.metadata["totaldisc"])
    #     self.assertEqual(audio["lyrics"][0], self.metadata["lyrics"])

   

    # def test_tag_aiff(self):
    #     input_file = os.path.join(self.test_files_dir, "ok.aiff")
    #     output_file = os.path.join(self.output_dir, "ok_tagged.aiff")
    #     shutil.copy(input_file, output_file)

    #     tagger = AudioTagger(output_file)
    #     tagger.tag_track(self.metadata, self.cover_file)

    #     audio = AIFF(output_file)
    #     self.assertEqual(audio["title"][0], self.metadata["title"])
    #     self.assertEqual(audio["artist"][0], self.metadata["artist"])
    #     self.assertEqual(audio["album"][0], self.metadata["album"])
    #     self.assertEqual(audio["tracknumber"][0], self.metadata["tracknumber"])
    #     self.assertEqual(audio["date"][0], self.metadata["date"])
    #     self.assertEqual(audio["genre"][0], self.metadata["genre"])
    #     self.assertEqual(audio["copyright"][0], self.metadata["copyright"])
    #     self.assertEqual(audio["discnumber"][0], self.metadata["discnumber"])
    #     self.assertEqual(audio["composer"][0], self.metadata["composer"])
    #     self.assertEqual(audio["isrc"][0], self.metadata["isrc"])
    #     self.assertEqual(audio["albumartist"][0], self.metadata["albumartist"])
    #     self.assertEqual(audio["totaldiscs"][0], self.metadata["totaldisc"])
    #     self.assertEqual(audio["lyrics"][0], self.metadata["lyrics"])

if __name__ == "__main__":
    unittest.main()
