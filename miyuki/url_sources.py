from abc import ABC, abstractmethod
import re
from typing import Optional
from miyuki.http_client import HttpClient
from miyuki.config import HREF_REGEX_PUBLIC_PLAYLIST, HREF_REGEX_NEXT_PAGE
from miyuki.logger import logger

class UrlSource(ABC):
    @abstractmethod
    def get_urls(self) -> list[str]:
        pass

class SingleUrlSource(UrlSource):
    def __init__(self, urls: list[str]):
        self.urls = urls

    def get_urls(self) -> list[str]:
        return self.urls

class PlaylistSource(UrlSource):
    def __init__(self, playlist_url: str, limit: Optional[str]):
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
                logger.info(f"Movie {len(movie_url_list)} url: {movie_url}")
                if self.limit and len(movie_url_list) >= self.limit:
                    return movie_url_list[:self.limit]
            next_page_matches = re.findall(HREF_REGEX_NEXT_PAGE, html_source)
            url = next_page_matches[0].replace('&amp;', '&') if next_page_matches else None
        return movie_url_list

class AuthSource(UrlSource):
    def __init__(self, username: str, password: str):
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
                logger.info(f"Movie {len(movie_url_list)} url: {movie_url}")
            next_page_matches = re.findall(HREF_REGEX_NEXT_PAGE, html_source)
            url = next_page_matches[0].replace('&amp;', '&') if next_page_matches else None
        return movie_url_list

class SearchSource(UrlSource):
    def __init__(self, key: str):
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
            return [temp_url_list[0]]
        logger.error(f"Search failed, key: {self.key}")
        return []

class FileSource(UrlSource):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_urls(self) -> list[str]:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        return urls