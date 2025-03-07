from abc import ABC, abstractmethod
import re
from typing import Optional
from miyuki.http_client import HttpClient
from miyuki.config import HREF_REGEX_PUBLIC_PLAYLIST, HREF_REGEX_NEXT_PAGE, MATCH_UUID_PATTERN
from miyuki.logger import logger
from miyuki.utils import ThreadSafeCounter
from enum import Enum

class UrlType(Enum):
    SINGLE = 1
    PLAYLIST = 2

class UrlSource(ABC):
    @abstractmethod
    def get_urls(self) -> list[str]:
        pass

    @staticmethod
    def movie_count_log(movie_counter: ThreadSafeCounter, movie_url: str):
        logger.info(f"Movie {movie_counter.increment_and_get()} url: {movie_url}")

class SingleUrlSource(UrlSource):
    def __init__(self, movie_counter: ThreadSafeCounter, urls: list[str]):
        self.movie_counter = movie_counter
        self.urls = urls

    def get_urls(self) -> list[str]:
        for url in self.urls:
            self.movie_count_log(self.movie_counter, url)
        return self.urls

class PlaylistSource(UrlSource):
    def __init__(self, movie_counter: ThreadSafeCounter, playlist_url: str, limit: Optional[str]):
        self.movie_counter = movie_counter
        self.playlist_url = playlist_url
        self.limit = int(limit) if limit else None
        self.http_client = HttpClient()

    def get_urls(self) -> list[str]:
        movie_url_list = []
        url = self.playlist_url
        while url and (self.limit is None or len(movie_url_list) < self.limit):
            html_source = self.http_client.get(url)
            if html_source is None:
                break
            html_source = html_source.decode('utf-8')
            movie_url_matches = re.findall(HREF_REGEX_PUBLIC_PLAYLIST, html_source)
            temp_url_list = list(set(movie_url_matches))
            for movie_url in temp_url_list:
                movie_url_list.append(movie_url)
                self.movie_count_log(self.movie_counter, movie_url)
                if self.limit and len(movie_url_list) >= self.limit:
                    return movie_url_list[:self.limit]
            next_page_matches = re.findall(HREF_REGEX_NEXT_PAGE, html_source)
            url = next_page_matches[0].replace('&amp;', '&') if next_page_matches else None
        return movie_url_list

class AutoUrlSource(UrlSource):
    def __init__(self, movie_counter: ThreadSafeCounter, auto_urls: list[str], limit: Optional[int]):
        self.movie_counter = movie_counter
        self.auto_urls = auto_urls
        self.limit = int(limit) if limit else None
        self.http_client = HttpClient()

    def get_urls(self) -> list[str]:
        movie_url_list = []

        need_url_total_now = self.limit

        for url in self.auto_urls:

            if need_url_total_now is not None:
                need_url_total_now = self.limit - len(movie_url_list)
                if need_url_total_now == 0:
                    break

            url_type : UrlType = self._determine_url_type(url)
            if url_type == UrlType.SINGLE:
                playlist_source = SingleUrlSource(self.movie_counter, [url])
                movie_url_list.extend(playlist_source.get_urls())
            else:
                playlist_source = PlaylistSource(self.movie_counter, url, need_url_total_now)
                movie_url_list.extend(playlist_source.get_urls())

        return movie_url_list

    def _determine_url_type(self, url: str) -> Optional[UrlType]:
        if self._is_movie_url(url):
            return UrlType.SINGLE
        else:
            return UrlType.PLAYLIST

    def _is_movie_url(self, url: str) -> bool:
        html = self.http_client.get(url)
        if not html:
            return False
        html = html.decode('utf-8')
        match = re.search(MATCH_UUID_PATTERN, html)
        if not match:
            return False
        return True

class AuthSource(UrlSource):
    def __init__(self, movie_counter: ThreadSafeCounter, username: str, password: str):
        self.movie_counter = movie_counter
        self.http_client = HttpClient()
        self.cookie = self._login(username, password)

    def _login(self, username: str, password: str) -> dict:
        response = self.http_client.post('https://missav.ai/api/login', data={'email': username, 'password': password})
        if response and response.status_code == 200:
            cookie_info = response.cookies.get_dict()
            if "user_uuid" in cookie_info:
                logger.info(f"User uuid: {cookie_info['user_uuid']}")
                return cookie_info
        logger.error("Login failed, check your network connection or account information.")
        exit(114514)

    def get_urls(self) -> list[str]:
        movie_url_list = []
        url = 'https://missav.ai/saved'
        while url:
            html_source = self.http_client.get(url, cookies=self.cookie)
            if html_source is None:
                break
            html_source = html_source.decode('utf-8')
            movie_url_matches = re.findall(HREF_REGEX_PUBLIC_PLAYLIST, html_source)
            temp_url_list = list(set(movie_url_matches))
            for movie_url in temp_url_list:
                movie_url_list.append(movie_url)
                self.movie_count_log(self.movie_counter, movie_url)
                # logger.info(f"Movie {len(movie_url_list)} url: {movie_url}")
            next_page_matches = re.findall(HREF_REGEX_NEXT_PAGE, html_source)
            url = next_page_matches[0].replace('&amp;', '&') if next_page_matches else None
        return movie_url_list

class SearchSource(UrlSource):
    def __init__(self, movie_counter: ThreadSafeCounter, key: str):
        self.movie_counter = movie_counter
        self.key = key
        self.http_client = HttpClient()

    def get_urls(self) -> list[str]:
        search_url = f"https://missav.ai/search/{self.key}"
        search_regex = r'<a href="([^"]+)" alt="' + self.key + '" >'
        html_source = self.http_client.get(search_url)
        if html_source is None:
            logger.error(f"Search failed, key: {self.key}")
            return []
        html_source = html_source.decode('utf-8')
        movie_url_matches = re.findall(search_regex, html_source)
        temp_url_list = list(set(movie_url_matches))
        if temp_url_list:
            logger.info(f"Search {self.key} successfully: {temp_url_list[0]}")
            self.movie_count_log(self.movie_counter, temp_url_list[0])
            return [temp_url_list[0]]
        logger.error(f"Search failed, key: {self.key}")
        return []

class FileSource(UrlSource):
    def __init__(self, movie_counter: ThreadSafeCounter, file_path: str):
        self.movie_counter = movie_counter
        self.file_path = file_path

    def get_urls(self) -> list[str]:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        for url in urls:
            self.movie_count_log(self.movie_counter, url)
        return urls