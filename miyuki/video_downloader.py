import os
import re
from typing import Optional, Tuple
import threading
from miyuki.config import MOVIE_SAVE_PATH_ROOT, MATCH_UUID_PATTERN, MATCH_TITLE_PATTERN, COVER_URL_PREFIX, TMP_HTML_FILE, RESOLUTION_PATTERN, VIDEO_M3U8_PREFIX, VIDEO_PLAYLIST_SUFFIX
from miyuki.http_client import HttpClient
from miyuki.logger import logger
from miyuki.utils import ThreadSafeCounter, display_progress_bar, split_integer_into_intervals, find_last_non_empty_line, find_closest
from miyuki.ffmpeg_processor import FFmpegProcessor


class VideoDownloader:
    def __init__(self, url: str, http_client: HttpClient, options: dict):
        self.url = url
        self.http_client = http_client
        self.movie_name = url.split('/')[-1]
        self.movie_folder = os.path.join(MOVIE_SAVE_PATH_ROOT, self.movie_name)
        self.options = options
        self.uuid = None
        self.title = None
        self.final_file_name = None
        self.counter = ThreadSafeCounter()

    def _fetch_metadata(self) -> bool:
        html = self.http_client.get(self.url)
        if not html:
            logger.error(f"Failed to fetch HTML for {self.url}")
            return False
        html = html.decode('utf-8')
        with open(TMP_HTML_FILE, 'w', encoding='utf-8') as file:
            file.write(html)
        match = re.search(MATCH_UUID_PATTERN, html)
        if not match:
            logger.error("Failed to match uuid.")
            return False
        result = match.group(1)
        self.uuid = "-".join(result.split("|")[::-1])
        logger.info(f"Matching uuid successfully: {self.uuid}")
        title_match = re.search(MATCH_TITLE_PATTERN, html)
        if title_match:
            illegal_chars = '<>:"/\|?* '
            origin_title = title_match.group(1)
            safe_title = origin_title
            for char in illegal_chars:
                safe_title = safe_title.replace(char, '_')
            if "uncensored" in self.url:
                safe_title += "_uncensored"
            self.title = safe_title
        return True

    def _download_cover(self) -> None:
        if not self.options.get('cover_action'):
            return
        cover_url = f"{COVER_URL_PREFIX}{self.movie_name}/cover-n.jpg"
        cover_content = self.http_client.get(cover_url)
        if cover_content:
            cover_path = os.path.join(MOVIE_SAVE_PATH_ROOT, f"{self.movie_name}-cover.jpg")
            with open(cover_path, 'wb') as f:
                f.write(cover_content)
        else:
            logger.error(f"Failed to download cover for {self.movie_name}")

    def _get_final_quality_and_resolution(self, playlist: str) -> Tuple[Optional[str], Optional[str]]:
        matches = re.findall(RESOLUTION_PATTERN, playlist)
        quality_map = {height: width for width, height in matches}
        quality_list = list(quality_map.keys())
        if not quality_list:
            logger.error("No resolutions found in playlist.")
            return None, None
        quality = self.options.get('quality')
        if quality is None:
            final_quality = quality_list[-1] + 'p'
            resolution_url = find_last_non_empty_line(playlist)
        else:
            target = int(quality)
            closest_height = find_closest([int(h) for h in quality_list], target)
            final_quality = str(closest_height) + 'p'
            url_type_x = f"{quality_map[str(closest_height)]}x{closest_height}/video.m3u8"
            url_type_p = f"{closest_height}p/video.m3u8"
            resolution_url = url_type_x if url_type_x in playlist else url_type_p if url_type_p in playlist else find_last_non_empty_line(playlist)
        return final_quality, resolution_url

    def _thread_task(self, start: int, end: int, uuid: str, resolution: str, video_offset_max: int) -> None:
        for i in range(start, end):
            url = f"https://surrit.com/{uuid}/{resolution}/video{i}.jpeg"
            content = self.http_client.get(url, retries=self.options.get('retry', 5), delay=self.options.get('delay', 2), timeout=self.options.get('timeout', 10))
            if content:
                file_path = os.path.join(self.movie_folder, f"video{i}.jpeg")
                with open(file_path, 'wb') as f:
                    f.write(content)
                display_progress_bar(video_offset_max + 1, self.counter)
            else:
                logger.error(f"Failed to download segment {i} for {self.movie_name}")

    def _download_segments(self, uuid: str, resolution: str, video_offset_max: int) -> None:
        if not self.options.get('download_action'):
            return
        intervals = split_integer_into_intervals(video_offset_max + 1, self.options.get('num_threads', os.cpu_count()))
        self.counter.reset()
        threads = []
        for start, end in intervals:
            thread = threading.Thread(target=self._thread_task, args=(start, end, uuid, resolution, video_offset_max))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        self.counter.reset()

    def _check_integrity(self, video_offset_max: int) -> None:
        downloaded_files = len([f for f in os.listdir(self.movie_folder) if f.endswith('.jpeg')])
        total_files = video_offset_max + 1
        integrity = downloaded_files / total_files
        logger.info(f"File integrity for {self.movie_name}: {integrity:.2%} ({downloaded_files}/{total_files} files)")

    def _assemble_video(self, video_offset_max: int) -> None:
        if not self.options.get('write_action'):
            return
        self.final_file_name = f"{self.movie_name}_{self.final_quality}"
        output_file = os.path.join(MOVIE_SAVE_PATH_ROOT, f"{self.final_file_name}.mp4")
        if self.options.get('ffmpeg_action'):
            segment_files = [os.path.join(self.movie_folder, f"video{i}.jpeg") for i in range(video_offset_max + 1) if os.path.exists(os.path.join(self.movie_folder, f"video{i}.jpeg"))]
            cover_file = os.path.join(MOVIE_SAVE_PATH_ROOT, f"{self.movie_name}-cover.jpg") if self.options.get('cover_as_preview') and os.path.exists(os.path.join(MOVIE_SAVE_PATH_ROOT, f"{self.movie_name}-cover.jpg")) else None
            FFmpegProcessor.create_video_from_segments(segment_files, output_file, cover_file)
        else:
            with open(output_file, 'wb') as outfile:
                for i in range(video_offset_max + 1):
                    file_path = os.path.join(self.movie_folder, f"video{i}.jpeg")
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as infile:
                            outfile.write(infile.read())
        if self.options.get('title_action') and self.title:
            os.rename(output_file, os.path.join(MOVIE_SAVE_PATH_ROOT, f"{self.title}.mp4"))

    def download(self) -> None:
        if not self._fetch_metadata():
            return
        playlist_url = f"{VIDEO_M3U8_PREFIX}{self.uuid}{VIDEO_PLAYLIST_SUFFIX}"
        playlist = self.http_client.get(playlist_url)
        if not playlist:
            logger.error("Failed to fetch playlist.")
            return
        playlist = playlist.decode('utf-8')
        self.final_quality, resolution_url = self._get_final_quality_and_resolution(playlist)
        if not self.final_quality:
            return
        video_m3u8_url = f"{VIDEO_M3U8_PREFIX}{self.uuid}/{resolution_url}"
        video_m3u8 = self.http_client.get(video_m3u8_url)
        if not video_m3u8:
            logger.error("Failed to fetch video m3u8.")
            return
        video_m3u8 = video_m3u8.decode('utf-8')
        video_offset_max_str = video_m3u8.splitlines()[-2]
        video_offset_max = int(re.search(r'\d+', video_offset_max_str).group(0))
        if not os.path.exists(self.movie_folder):
            os.makedirs(self.movie_folder)
        self._download_cover()
        self._download_segments(self.uuid, resolution_url.split('/')[0], video_offset_max)
        self._check_integrity(video_offset_max)
        self._assemble_video(video_offset_max)
