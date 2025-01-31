#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   printf.py
@Time    :   2020/08/16
@Author  :   Yaronzz
@Version :   3.0
@Contact :   yaronhuang@foxmail.com
@Desc    :   Print with colors and logging
'''
import threading
import aigpy
import prettytable
from typing import List, Any, Optional

import apiKey

from model import *
from paths import *
from settings import *
from lang.language import *
from custom.logger import Logger, LoggerConfig, LogLevel

VERSION = '2022.10.31.1'
__LOGO__ = f'''
 /$$$$$$$$ /$$       /$$           /$$               /$$ /$$
|__  $$__/|__/      | $$          | $$              | $$| $$
   | $$    /$$  /$$$$$$$  /$$$$$$ | $$          /$$$$$$$| $$
   | $$   | $$ /$$__  $$ |____  $$| $$ /$$$$$$ /$$__  $$| $$
   | $$   | $$| $$  | $$  /$$$$$$$| $$|______/| $$  | $$| $$
   | $$   | $$| $$  | $$ /$$__  $$| $$        | $$  | $$| $$
   | $$   | $$|  $$$$$$$|  $$$$$$$| $$        |  $$$$$$$| $$
   |__/   |__/ \_______/ \_______/|__/         \_______/|__/

       https://github.com/yaronzz/Tidal-Media-Downloader

                        {VERSION}
'''

print_mutex = threading.Lock()

class Printf(object):
    """Class for handling formatted console output and logging."""
    
    logger = Logger(LoggerConfig(
        name="tidal-dl",
        level=LogLevel.INFO
    ).create())

    @staticmethod
    def logo() -> None:
        """Print and log the application logo."""
        print(__LOGO__)
        Printf.logger.info(__LOGO__)

    @staticmethod
    def __gettable__(columns: List[str], rows: List[List[Any]]) -> prettytable.PrettyTable:
        """Create a formatted table with colored columns."""
        tb = prettytable.PrettyTable()
        tb.field_names = list(aigpy.cmd.green(item) for item in columns)
        tb.align = 'l'
        for item in rows:
            tb.add_row(item)
        return tb

    @staticmethod
    def usage() -> None:
        """Print usage information."""
        print("=============TIDAL-DL HELP==============")
        tb = Printf.__gettable__(["OPTION", "DESC"], [
            ["-h or --help",        "show help-message"],
            ["-v or --version",     "show version"],
            ["-g or --gui",         "show simple-gui"],
            ["-o or --output",      "download path"],
            ["-l or --link",        "url/id/filePath"],
            ["-q or --quality",     "track quality('Normal','High,'HiFi','Master')"],
            ["-r or --resolution",  "video resolution('P1080', 'P720', 'P480', 'P360')"]
        ])
        print(tb)

    @staticmethod
    def checkVersion() -> None:
        """Check for new version availability."""
        onlineVer = aigpy.pip.getLastVersion('tidal-dl')
        if onlineVer is not None:
            icmp = aigpy.system.cmpVersion(onlineVer, VERSION)
            if icmp > 0:
                Printf.info(LANG.select.PRINT_LATEST_VERSION + ' ' + onlineVer)

    @staticmethod
    def settings() -> None:
        """Print current settings."""
        data = SETTINGS
        tb = Printf.__gettable__([LANG.select.SETTING, LANG.select.VALUE], [
            #settings - path and format
            [LANG.select.SETTING_PATH, getProfilePath()],
            [LANG.select.SETTING_DOWNLOAD_PATH, data.downloadPath],
            [LANG.select.SETTING_ALBUM_FOLDER_FORMAT, data.albumFolderFormat],
            [LANG.select.SETTING_PLAYLIST_FOLDER_FORMAT, data.playlistFolderFormat],
            [LANG.select.SETTING_TRACK_FILE_FORMAT, data.trackFileFormat],
            [LANG.select.SETTING_VIDEO_FILE_FORMAT, data.videoFileFormat],

            #settings - quality
            [LANG.select.SETTING_AUDIO_QUALITY, data.audioQuality],
            [LANG.select.SETTING_VIDEO_QUALITY, data.videoQuality],

            #settings - else
            [LANG.select.SETTING_USE_PLAYLIST_FOLDER, data.usePlaylistFolder],
            [LANG.select.SETTING_CHECK_EXIST, data.checkExist],
            [LANG.select.SETTING_SHOW_PROGRESS, data.showProgress],
            [LANG.select.SETTING_SHOW_TRACKINFO, data.showTrackInfo],
            [LANG.select.SETTING_SAVE_ALBUMINFO, data.saveAlbumInfo],
            [LANG.select.SETTING_DOWNLOAD_VIDEOS, data.downloadVideos],
            [LANG.select.SETTING_SAVE_COVERS, data.saveCovers],
            [LANG.select.SETTING_INCLUDE_EP, data.includeEP],
            [LANG.select.SETTING_LANGUAGE, LANG.getLangName(data.language)],
            [LANG.select.SETTING_ADD_LRC_FILE, data.lyricFile],
            [LANG.select.SETTING_MULITHREAD_DOWNLOAD, data.multiThread],
            [LANG.select.SETTING_APIKEY, f"[{data.apiKeyIndex}]" + apiKey.getItem(data.apiKeyIndex)['formats']],
            [LANG.select.SETTING_DOWNLOAD_DELAY, data.downloadDelay],
        ])
        print(tb)
        Printf.logger.debug("Settings displayed")

    @staticmethod
    def choices() -> None:
        """Print available choices."""
        print("====================================================")
        tb = Printf.__gettable__([LANG.select.CHOICE, LANG.select.FUNCTION], [
            [aigpy.cmd.green(LANG.select.CHOICE_ENTER + " '0':"), LANG.select.CHOICE_EXIT],
            [aigpy.cmd.green(LANG.select.CHOICE_ENTER + " '1':"), LANG.select.CHOICE_LOGIN],
            [aigpy.cmd.green(LANG.select.CHOICE_ENTER + " '2':"), LANG.select.CHOICE_LOGOUT],
            [aigpy.cmd.green(LANG.select.CHOICE_ENTER + " '3':"), LANG.select.CHOICE_SET_ACCESS_TOKEN],
            [aigpy.cmd.green(LANG.select.CHOICE_ENTER + " '4':"), LANG.select.CHOICE_SETTINGS + '-Path'],
            [aigpy.cmd.green(LANG.select.CHOICE_ENTER + " '5':"), LANG.select.CHOICE_SETTINGS + '-Quality'],
            [aigpy.cmd.green(LANG.select.CHOICE_ENTER + " '6':"), LANG.select.CHOICE_SETTINGS + '-Else'],
            [aigpy.cmd.green(LANG.select.CHOICE_ENTER + " '7':"), LANG.select.CHOICE_APIKEY],
            [aigpy.cmd.green(LANG.select.CHOICE_ENTER_URLID), LANG.select.CHOICE_DOWNLOAD_BY_URL],
        ])
        tb.set_style(prettytable.PLAIN_COLUMNS)
        print(tb)
        print("====================================================")

    @staticmethod
    def enter(string: str) -> str:
        """Get user input with colored prompt."""
        aigpy.cmd.colorPrint(string, aigpy.cmd.TextColor.Yellow, None)
        return input("")

    @staticmethod
    def enterBool(string: str) -> bool:
        """Get boolean user input."""
        aigpy.cmd.colorPrint(string, aigpy.cmd.TextColor.Yellow, None)
        return input("") == '1'

    @staticmethod
    def enterPath(string: str, errmsg: str, retWord: str = '0', default: str = "") -> str:
        """Get path input from user with validation."""
        while True:
            ret = aigpy.cmd.inputPath(aigpy.cmd.yellow(string), retWord)
            if ret == retWord:
                return default
            elif ret == "":
                Printf.err(errmsg)
            else:
                break
        return ret

    @staticmethod
    def enterLimit(string: str, errmsg: str, limit: List[str] = []) -> Optional[str]:
        """Get limited choice input from user."""
        while True:
            ret = aigpy.cmd.inputLimit(aigpy.cmd.yellow(string), limit)
            if ret is None:
                Printf.err(errmsg)
            else:
                break
        return ret

    @staticmethod
    def enterFormat(string: str, current: str, default: str) -> str:
        """Get format input from user."""
        ret = Printf.enter(string)
        if ret == '0' or aigpy.string.isNull(ret):
            return current
        if ret.lower() == 'default':
            return default
        return ret

    @staticmethod
    def err(string: str) -> None:
        """Print and log error message."""
        with print_mutex:
            print(aigpy.cmd.red(LANG.select.PRINT_ERR + " ") + string)
            Printf.logger.error(string)

    @staticmethod
    def info(string: str) -> None:
        """Print and log info message."""
        with print_mutex:
            print(aigpy.cmd.blue(LANG.select.PRINT_INFO + " ") + string)
            Printf.logger.info(string)

    @staticmethod
    def success(string: str) -> None:
        """Print and log success message."""
        with print_mutex:
            print(aigpy.cmd.green(LANG.select.PRINT_SUCCESS + " ") + string)
            Printf.logger.info(string)

    @staticmethod
    def album(data: Album) -> None:
        """Print and log album information."""
        tb = Printf.__gettable__([LANG.select.MODEL_ALBUM_PROPERTY, LANG.select.VALUE], [
            [LANG.select.MODEL_TITLE, data.title],
            ["ID", data.id],
            [LANG.select.MODEL_TRACK_NUMBER, data.numberOfTracks],
            [LANG.select.MODEL_VIDEO_NUMBER, data.numberOfVideos],
            [LANG.select.MODEL_RELEASE_DATE, data.releaseDate],
            [LANG.select.MODEL_VERSION, data.version],
            [LANG.select.MODEL_EXPLICIT, data.explicit],
        ])
        print(tb)
        Printf.logger.info(f"Album: {data.title} (ID: {data.id}) - {data.numberOfTracks} tracks, {data.numberOfVideos} videos")

    @staticmethod
    def track(data: Track, stream: Optional[StreamUrl] = None) -> None:
        """Print and log track information."""
        tb = Printf.__gettable__([LANG.select.MODEL_TRACK_PROPERTY, LANG.select.VALUE], [
            [LANG.select.MODEL_TITLE, data.title],
            ["ID", data.id],
            [LANG.select.MODEL_ALBUM, data.album.title],
            [LANG.select.MODEL_VERSION, data.version],
            [LANG.select.MODEL_EXPLICIT, data.explicit],
            ["Max-Q", data.audioQuality],
        ])
        if stream is not None:
            tb.add_row(["Get-Q", str(stream.soundQuality)])
            tb.add_row(["Get-Codec", str(stream.codec)])
        print(tb)
        Printf.logger.info(f"Track: {data.title} (ID: {data.id}) - Album: {data.album.title}")

    @staticmethod
    def video(data: Video, stream: Optional[VideoStreamUrl] = None) -> None:
        """Print and log video information."""
        tb = Printf.__gettable__([LANG.select.MODEL_VIDEO_PROPERTY, LANG.select.VALUE], [
            [LANG.select.MODEL_TITLE, data.title],
            [LANG.select.MODEL_ALBUM, data.album.title if data.album is not None else None],
            [LANG.select.MODEL_VERSION, data.version],
            [LANG.select.MODEL_EXPLICIT, data.explicit],
            ["Max-Q", data.quality],
        ])
        if stream is not None:
            tb.add_row(["Get-Q", str(stream.resolution)])
            tb.add_row(["Get-Codec", str(stream.codec)])
        print(tb)
        Printf.logger.info(f"Video: {data.title} (ID: {data.id})")

    @staticmethod
    def artist(data: Artist, num: int) -> None:
        """Print and log artist information."""
        tb = Printf.__gettable__([LANG.select.MODEL_ARTIST_PROPERTY, LANG.select.VALUE], [
            [LANG.select.MODEL_ID, data.id],
            [LANG.select.MODEL_NAME, data.name],
            ["Number of albums", num],
            [LANG.select.MODEL_TYPE, str(data.type)],
        ])
        print(tb)
        Printf.logger.info(f"Artist: {data.name} (ID: {data.id}) - {num} albums")

    @staticmethod
    def playlist(data: Any) -> None:
        """Print and log playlist information."""
        tb = Printf.__gettable__([LANG.select.MODEL_PLAYLIST_PROPERTY, LANG.select.VALUE], [
            [LANG.select.MODEL_TITLE, data.title],
            [LANG.select.MODEL_TRACK_NUMBER, data.numberOfTracks],
            [LANG.select.MODEL_VIDEO_NUMBER, data.numberOfVideos],
        ])
        print(tb)
        Printf.logger.info(f"Playlist: {data.title} - {data.numberOfTracks} tracks, {data.numberOfVideos} videos")

    @staticmethod
    def mix(data: Any) -> None:
        """Print and log mix information."""
        tb = Printf.__gettable__([LANG.select.MODEL_PLAYLIST_PROPERTY, LANG.select.VALUE], [
            [LANG.select.MODEL_ID, data.id],
            [LANG.select.MODEL_TRACK_NUMBER, len(data.tracks)],
            [LANG.select.MODEL_VIDEO_NUMBER, len(data.videos)],
        ])
        print(tb)
        Printf.logger.info(f"Mix (ID: {data.id}) - {len(data.tracks)} tracks, {len(data.videos)} videos")

    @staticmethod
    def apikeys(items: List[dict]) -> None:
        """Print API keys information."""
        print("-------------API-KEYS---------------")
        tb = prettytable.PrettyTable()
        tb.field_names = [aigpy.cmd.green('Index'),
                         aigpy.cmd.green('Valid'),
                         aigpy.cmd.green('Platform'),
                         aigpy.cmd.green('Formats'), ]
        tb.align = 'l'

        for index, item in enumerate(items):
            tb.add_row([str(index),
                       aigpy.cmd.green('True') if item["valid"] == "True" else aigpy.cmd.red('False'),
                       item["platform"],
                       item["formats"]])
        print(tb)
        Printf.logger.debug("API keys displayed")
