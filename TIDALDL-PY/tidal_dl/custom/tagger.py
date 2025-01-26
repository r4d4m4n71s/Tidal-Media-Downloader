from mutagen.flac import FLAC, Picture
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TDRC, TCON, TCOP, TPOS, TCOM, TSRC, TPE2, USLT, APIC
from mutagen import MutagenError
from audio_codifier import AudioCodifier, AudioCodec
from logger import *

class AudioTagger:
    
    def __init__(self, file_path):
        self.AudioCodifier = AudioCodifier()
        self.file_path = file_path
        self.audioCodec = self.AudioCodifier.get_codec_from_extension(self.file_path)        
        
    def _try_get_metadata_from_file(self):
        try:
            logger.info(f"Loading metadata for: {self.file_path}")
            return self._get_audio_file()
        except MutagenError as e:
            logger.error(f"Failed to load metadata for: {self.file_path} due to {e}")
            return self._attempt_reencode_and_load()

    def _attempt_reencode_and_load(self):
        codecs_to_try = [None, AudioCodec.wav, AudioCodec.mp3]
        for codec in codecs_to_try:
            try:
                self.file_path = self.AudioCodifier.reencode_audio(self.file_path, codec=codec)
                audio = self._get_audio_file()
                self.audioCodec = codec
                return audio
            except Exception as e:
                logger.error(f"Failed to reencode and load metadata for: {self.file_path} with codec {codec} due to {e}")
        return None

    def _get_audio_file(self):
        codec_to_class = {
            AudioCodec.flac: FLAC,
            AudioCodec.mp3: lambda path: MP3(path, ID3=ID3),
            AudioCodec.aac: MP4,
            AudioCodec.opus: OggVorbis,
            AudioCodec.wav: WAVE
        }
        audio_class = codec_to_class.get(self.audioCodec)
        if audio_class:
            return audio_class(self.file_path)
        else:
            raise RuntimeError(f"Unsupported file format: {self.file_path}")

    def tag_track(self, metadata, cover_art_path=None):
        
        audio = self._try_get_metadata_from_file()
        
        if audio is None:
            raise RuntimeError(f"Cannot tag {self.file_path} because audio metadata could not be loaded.")
        try:
            tag_method = self._get_tag_method()
            tag_method(audio, metadata, cover_art_path)
        except Exception as e:
            raise RuntimeError(f"Failed to tag {self.file_path}") from e

    def _get_tag_method(self):
        codec_to_method = {
            AudioCodec.flac: self._tag_flac,
            AudioCodec.mp3: self._tag_mp3,
            AudioCodec.aac: self._tag_aac,
            AudioCodec.opus: self._tag_ogg,
            AudioCodec.wav: self._tag_wav
        }
        tag_method = codec_to_method.get(self.audioCodec)
        if not tag_method:
            raise RuntimeError(f"Unsupported file: {self.file_path}")
        return tag_method

    def _tag_flac(self, audio, metadata, cover_art_path=None):
        self._apply_common_metadata(audio, metadata, cover_art_path)
        audio.save()
        logger.info(f"Successfully tagged {self.file_path} (FLAC) with metadata: {metadata.get('title', '')}")

    def _tag_mp3(self, audio, metadata, cover_art_path=None):
        if audio.tags is None:
            audio.add_tags()
        self._apply_common_metadata(audio, metadata, cover_art_path)
        audio.save()
        logger.info(f"Successfully tagged {self.file_path} (MP3) with metadata: {metadata.get('title', '')}")

    def _tag_aac(self, audio, metadata, cover_art_path=None):
        self._apply_common_metadata(audio, metadata, cover_art_path)
        audio.save()
        logger.info(f"Successfully tagged {self.file_path} (AAC) with metadata: {metadata.get('title', '')}")

    def _tag_ogg(self, audio, metadata, cover_art_path=None):
        self._apply_common_metadata(audio, metadata)
        audio.save()
        logger.info(f"Successfully tagged {self.file_path} (OGG) with metadata: {metadata.get('title', '')}")

    def _tag_wav(self, audio, metadata, cover_art_path=None):
        self._apply_common_metadata(audio, metadata)
        audio.save()
        logger.info(f"Successfully tagged {self.file_path} (WAV) with metadata: {metadata.get('title', '')}")

    def _apply_common_metadata(self, audio, metadata, cover_art_path=None):
        if hasattr(audio, "tags"):
            self._apply_tags(audio, metadata)
            if cover_art_path and isinstance(audio, FLAC):
                self._add_flac_cover_art(audio, cover_art_path)
        if self.audioCodec == AudioCodec.mp3:
            self._apply_id3_tags(audio, metadata)
            if cover_art_path:
                self._add_mp3_cover_art(audio, cover_art_path)
        elif self.audioCodec == AudioCodec.aac:
            self._apply_mp4_tags(audio, metadata)
            if cover_art_path:
                self._add_aac_cover_art(audio, cover_art_path)
        logger.info(f"Successfully tagged {self.file_path} ({self.audioCodec.name.upper()}) with metadata: {metadata.get('title', '')}")

    # Function to rewrite a tuple if it exists or add it otherwise
    def update_or_add_tuple(self, lst, new_tuple):
        key = new_tuple[0]  # Assume the first element is the key
        found = False

        # Iterate through the list to find the tuple with the same key
        for i, (existing_key, *_) in enumerate(lst):
            if existing_key == key:
                lst[i] = new_tuple  # Rewrite the tuple
                found = True
                break

        if not found:
            lst.append(new_tuple)  # Add the tuple if it doesn't exist

    def _apply_tags(self, audio, metadata):

        if not audio.tags:
            audio.tags = []

        self.update_or_add_tuple(audio.tags, ("title", metadata.get("title", "")))
        self.update_or_add_tuple(audio.tags, ("artist", metadata.get("artist", "")))
        self.update_or_add_tuple(audio.tags, ("album", metadata.get("album", "")))
        self.update_or_add_tuple(audio.tags, ("tracknumber", metadata.get("tracknumber", "")))
        self.update_or_add_tuple(audio.tags, ("date", metadata.get("date", "")))
        self.update_or_add_tuple(audio.tags, ("genre", metadata.get("genre", "")))
        self.update_or_add_tuple(audio.tags, ("copyright", metadata.get("copyright", "")))
        self.update_or_add_tuple(audio.tags, ("discnumber", metadata.get("discnumber", "")))
        self.update_or_add_tuple(audio.tags, ("composer", metadata.get("composer", "")))
        self.update_or_add_tuple(audio.tags, ("isrc", metadata.get("isrc", "")))
        self.update_or_add_tuple(audio.tags, ("albumartist", metadata.get("albumartist", "")))
        self.update_or_add_tuple(audio.tags, ("totaldisc", metadata.get("totaldisc", "")))
        self.update_or_add_tuple(audio.tags, ("lyrics", metadata.get("lyrics", "")))
        
    def _apply_id3_tags(self, audio, metadata):
        audio.tags.add(TIT2(encoding=3, text=metadata.get("title", "")))
        audio.tags.add(TPE1(encoding=3, text=metadata.get("artist", "")))
        audio.tags.add(TALB(encoding=3, text=metadata.get("album", "")))
        audio.tags.add(TRCK(encoding=3, text=metadata.get("tracknumber", "")))
        audio.tags.add(TDRC(encoding=3, text=metadata.get("date", "")))
        audio.tags.add(TCON(encoding=3, text=metadata.get("genre", "")))
        audio.tags.add(TCOP(encoding=3, text=metadata.get("copyright", "")))
        audio.tags.add(TPOS(encoding=3, text=f"{metadata.get('discnumber', '')}/{metadata.get('totaldisc', '')}"))
        audio.tags.add(TCOM(encoding=3, text=metadata.get("composer", "")))
        audio.tags.add(TSRC(encoding=3, text=metadata.get("isrc", "")))
        audio.tags.add(TPE2(encoding=3, text=metadata.get("albumartist", "")))
        audio.tags.add(USLT(encoding=3, lang='eng', desc='', text=metadata.get("lyrics", "")))

    def _apply_mp4_tags(self, audio, metadata):
        audio["\xa9nam"] = metadata.get("title", "")
        audio["\xa9ART"] = metadata.get("artist", "")
        audio["\xa9alb"] = metadata.get("album", "")
        audio["trkn"] = [(int(metadata.get("tracknumber", 0)), 0)]
        audio["\xa9day"] = metadata.get("date", "")
        audio["\xa9gen"] = metadata.get("genre", "")
        audio["cprt"] = metadata.get("copyright", "")
        audio["disk"] = [(int(metadata.get("discnumber", 0)), int(metadata.get("totaldisc", 0)))]
        audio["\xa9wrt"] = metadata.get("composer", "")
        audio["----:com.apple.iTunes:ISRC"] = metadata.get("isrc", "").encode("utf-8")
        audio["aART"] = metadata.get("albumartist", "")
        audio["\xa9lyr"] = metadata.get("lyrics", "")

    def _add_flac_cover_art(self, audio, cover_art_path):
        picture = Picture()
        picture.type = 3  # Front cover
        picture.mime = "image/jpeg" if cover_art_path.lower().endswith(".jpg") else "image/png"
        with open(cover_art_path, "rb") as f:
            picture.data = f.read()
        audio.add_picture(picture)

    def _add_mp3_cover_art(self, audio, cover_art_path):
        with open(cover_art_path, "rb") as f:
            cover_data = f.read()
        audio.tags.add(APIC(
            encoding=3,  # UTF-8
            mime="image/jpeg" if cover_art_path.lower().endswith(".jpg") else "image/png",
            type=3,  # Front cover
            desc="Cover",
            data=cover_data
        ))

    def _add_aac_cover_art(self, audio, cover_art_path):
        with open(cover_art_path, "rb") as f:
            cover_data = f.read()
        audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG if cover_art_path.lower().endswith(".jpg") else MP4Cover.FORMAT_PNG)]