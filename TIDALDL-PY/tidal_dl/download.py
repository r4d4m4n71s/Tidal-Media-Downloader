#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   download.py
@Time    :   2020/11/08
@Author  :   Yaronzz
@Version :   1.0
@Contact :   yaronhuang@foxmail.com
@Desc    :   Download handler for Tidal content
'''

from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Tuple, Dict, Any, Union
import os
import requests

from decryption import *
from printf import *
from tidal import *
from custom.logger import Logger, LoggerConfig, LogLevel

# Initialize logger
logger = Logger(LoggerConfig(
    name="tidal-dl-download",
    level=LogLevel.INFO
).create())

def __isSkip__(finalpath: str, url: str) -> bool:
    """Check if download can be skipped."""
    if not SETTINGS.checkExist:
        return False
    curSize = aigpy.file.getSize(finalpath)
    if curSize <= 0:
        return False
    netSize = aigpy.net.getSize(url)
    return curSize >= netSize

def __encrypted__(stream: StreamUrl, srcPath: str, descPath: str) -> None:
    """Handle file encryption/decryption."""
    try:
        if aigpy.string.isNull(stream.encryptionKey):
            os.replace(srcPath, descPath)
        else:
            key, nonce = decrypt_security_token(stream.encryptionKey)
            decrypt_file(srcPath, descPath, key, nonce)
            os.remove(srcPath)
        logger.debug(f"Encryption handled for {descPath}")
    except Exception as e:
        logger.error(f"Encryption error for {descPath}: {str(e)}")
        raise

def __parseContributors__(roleType: str, Contributors: Optional[Dict[str, Any]]) -> Optional[List[str]]:
    """Parse contributors for a specific role."""
    if Contributors is None:
        return None
    try:
        ret = []
        for item in Contributors['items']:
            if item['role'] == roleType:
                ret.append(item['name'])
        return ret
    except Exception as e:
        logger.warning(f"Failed to parse contributors for role {roleType}: {str(e)}")
        return None

def __setMetaData__(track: Track, album: Album, filepath: str, contributors: Optional[Dict[str, Any]], lyrics: str) -> None:
    """Set metadata for audio file."""
    try:
        obj = aigpy.tag.TagTool(filepath)
        obj.album = track.album.title
        obj.title = track.title
        if not aigpy.string.isNull(track.version):
            obj.title += f' ({track.version})'

        obj.artist = list(map(lambda artist: artist.name, track.artists))
        obj.copyright = track.copyRight
        obj.tracknumber = track.trackNumber
        obj.discnumber = track.volumeNumber
        obj.composer = __parseContributors__('Composer', contributors)
        obj.isrc = track.isrc

        obj.albumartist = list(map(lambda artist: artist.name, album.artists))
        obj.date = album.releaseDate
        obj.totaldisc = album.numberOfVolumes
        obj.lyrics = lyrics
        if obj.totaldisc <= 1:
            obj.totaltrack = album.numberOfTracks
        
        coverpath = TIDAL_API.getCoverUrl(album.cover, "1280", "1280")
        obj.save(coverpath)
        logger.debug(f"Metadata set for {filepath}")
    except Exception as e:
        logger.error(f"Failed to set metadata for {filepath}: {str(e)}")
        raise

def downloadCover(album: Optional[Album]) -> None:
    """Download album cover."""
    if album is None:
        return
    try:
        path = getAlbumPath(album) + '/cover.jpg'
        url = TIDAL_API.getCoverUrl(album.cover, "1280", "1280")
        aigpy.net.downloadFile(url, path)
        logger.debug(f"Cover downloaded for album {album.title}")
    except Exception as e:
        logger.error(f"Failed to download cover for album {album.title}: {str(e)}")

def downloadAlbumInfo(album: Optional[Album], tracks: List[Track]) -> None:
    """Download album information to text file."""
    if album is None:
        return

    try:
        path = getAlbumPath(album)
        aigpy.path.mkdirs(path)
        path += '/AlbumInfo.txt'

        infos = [
            f"[ID]          {str(album.id)}",
            f"[Title]       {str(album.title)}",
            f"[Artists]     {TIDAL_API.getArtistsName(album.artists)}",
            f"[ReleaseDate] {str(album.releaseDate)}",
            f"[SongNum]     {str(album.numberOfTracks)}",
            f"[Duration]    {str(album.duration)}",
            ""
        ]

        for index in range(0, album.numberOfVolumes):
            volumeNumber = index + 1
            infos.append(f"===========CD {volumeNumber}=============")
            for item in tracks:
                if item.volumeNumber != volumeNumber:
                    continue
                infos.append('{:<8}'.format(f"[{item.trackNumber}]") + item.title)

        aigpy.file.write(path, '\n'.join(infos), "w+")
        logger.debug(f"Album info written for {album.title}")
    except Exception as e:
        logger.error(f"Failed to write album info for {album.title}: {str(e)}")

def downloadVideo(video: Video, album: Optional[Album] = None, playlist: Optional[Playlist] = None) -> Tuple[bool, str]:
    """Download a video."""
    try:
        stream = TIDAL_API.getVideoStreamUrl(video.id, SETTINGS.videoQuality)
        path = getVideoPath(video, album, playlist)

        Printf.video(video, stream)
        logger.info(f"Downloading video: {video.title}")
        logger.debug(f"Video URL: {stream.m3u8Url}")

        m3u8content = requests.get(stream.m3u8Url).content
        if m3u8content is None:
            error_msg = f"Failed to get M3U8 content for video {video.title}"
            logger.error(error_msg)
            Printf.err(error_msg)
            return False, error_msg

        urls = aigpy.m3u8.parseTsUrls(m3u8content)
        if len(urls) <= 0:
            error_msg = f"No TS URLs found for video {video.title}"
            logger.error(error_msg)
            Printf.err(error_msg)
            return False, error_msg

        check, msg = aigpy.m3u8.downloadByTsUrls(urls, path)
        if check:
            logger.info(f"Successfully downloaded video: {video.title}")
            Printf.success(video.title)
            return True, ""
        else:
            error_msg = f"Failed to download video {video.title}: {msg}"
            logger.error(error_msg)
            Printf.err(error_msg)
            return False, msg

    except Exception as e:
        error_msg = f"Error downloading video {video.title}: {str(e)}"
        logger.error(error_msg)
        Printf.err(error_msg)
        return False, str(e)

def downloadTrack(track: Track, album: Optional[Album] = None, playlist: Optional[Playlist] = None, 
                 userProgress: Any = None, partSize: int = 1048576) -> Tuple[bool, str]:
    """Download a track."""
    try:
        stream = TIDAL_API.getStreamUrl(track.id, SETTINGS.audioQuality)
        path = getTrackPath(track, stream, album, playlist)

        if SETTINGS.showTrackInfo and not SETTINGS.multiThread:
            Printf.track(track, stream)

        if userProgress is not None:
            userProgress.updateStream(stream)

        logger.info(f"Processing track: {track.title}")

        # Check if download can be skipped
        if __isSkip__(path, stream.url):
            logger.info(f"Skipping {track.title} (already exists)")
            Printf.success(f"{aigpy.path.getFileName(path)} (skip:already exists!)")
            return True, ''

        # Download track
        logger.debug(f"Downloading from URL: {stream.url}")
        tool = aigpy.download.DownloadTool(path + '.part', stream.urls)
        tool.setUserProgress(userProgress)
        tool.setPartSize(partSize)
        check, err = tool.start(SETTINGS.showProgress and not SETTINGS.multiThread)
        
        if not check:
            error_msg = f"Download failed for {track.title}: {str(err)}"
            logger.error(error_msg)
            Printf.err(error_msg)
            return False, str(err)

        # Handle encryption
        __encrypted__(stream, path + '.part', path)

        # Get contributors
        try:
            contributors = TIDAL_API.getTrackContributors(track.id)
        except Exception as e:
            logger.warning(f"Failed to get contributors for {track.title}: {str(e)}")
            contributors = None

        # Get lyrics
        try:
            lyrics = TIDAL_API.getLyrics(track.id).subtitles
            if SETTINGS.lyricFile:
                lrcPath = path.rsplit(".", 1)[0] + '.lrc'
                aigpy.file.write(lrcPath, lyrics, 'w')
                logger.debug(f"Lyrics saved to {lrcPath}")
        except Exception as e:
            logger.warning(f"Failed to get lyrics for {track.title}: {str(e)}")
            lyrics = ''

        # Set metadata
        __setMetaData__(track, album, path, contributors, lyrics)
        
        logger.info(f"Successfully downloaded and processed: {track.title}")
        Printf.success(track.title)
        return True, ''

    except Exception as e:
        error_msg = f"Error processing track {track.title}: {str(e)}"
        logger.error(error_msg)
        Printf.err(error_msg)
        return False, str(e)

def downloadTracks(tracks: List[Track], album: Optional[Album] = None, playlist: Optional[Playlist] = None) -> None:
    """Download multiple tracks."""
    def __getAlbum__(item: Track) -> Album:
        album = TIDAL_API.getAlbum(item.album.id)
        if SETTINGS.saveCovers and not SETTINGS.usePlaylistFolder:
            downloadCover(album)
        return album

    logger.info(f"Starting download of {len(tracks)} tracks")

    if not SETTINGS.multiThread:
        for index, item in enumerate(tracks):
            itemAlbum = album
            if itemAlbum is None:
                itemAlbum = __getAlbum__(item)
                item.trackNumberOnPlaylist = index + 1
            downloadTrack(item, itemAlbum, playlist)
    else:
        logger.info("Using multi-threaded download")
        thread_pool = ThreadPoolExecutor(max_workers=5)
        for index, item in enumerate(tracks):
            itemAlbum = album
            if itemAlbum is None:
                itemAlbum = __getAlbum__(item)
                item.trackNumberOnPlaylist = index + 1
            thread_pool.submit(downloadTrack, item, itemAlbum, playlist)
        thread_pool.shutdown(wait=True)

    logger.info("Track download process completed")

def downloadVideos(videos: List[Video], album: Album, playlist: Optional[Playlist] = None) -> None:
    """Download multiple videos."""
    logger.info(f"Starting download of {len(videos)} videos")
    for item in videos:
        downloadVideo(item, album, playlist)
    logger.info("Video download process completed")
