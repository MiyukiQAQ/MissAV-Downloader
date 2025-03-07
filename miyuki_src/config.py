RECORD_FILE = 'downloaded_urls_miyuki.txt'
FFMPEG_INPUT_FILE = 'ffmpeg_input_miyuki.txt'
TMP_HTML_FILE = 'tmp_movie_miyuki.html'
MOVIE_SAVE_PATH_ROOT = 'movies_folder_miyuki'
COVER_URL_PREFIX = 'https://fourhoi.com/'
VIDEO_M3U8_PREFIX = 'https://surrit.com/'
VIDEO_PLAYLIST_SUFFIX = '/playlist.m3u8'
HREF_REGEX_MOVIE_COLLECTION = r'<a class="text-secondary group-hover:text-primary" href="([^"]+)" alt="'
HREF_REGEX_PUBLIC_PLAYLIST = r'<a href="([^"]+)" alt="'
HREF_REGEX_NEXT_PAGE = r'<a href="([^"]+)" rel="next"'
MATCH_UUID_PATTERN = r'm3u8\|([a-f0-9\|]+)\|com\|surrit\|https\|video'
MATCH_TITLE_PATTERN = r'<title>([^"]+)</title>'
RESOLUTION_PATTERN = r'RESOLUTION=(\d+)x(\d+)'
MAGIC_NUMBER = 114514
RETRY = 5
DELAY = 2
TIMEOUT = 10
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}
