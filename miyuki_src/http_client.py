from typing import Optional
import time
from curl_cffi import requests
from config import HEADERS, RETRY, DELAY, TIMEOUT
from logger import logger


class HttpClient:
    def get(self, url: str, cookies: Optional[dict] = None, retries: int = RETRY, delay: int = DELAY, timeout: int = TIMEOUT) -> Optional[bytes]:
        for attempt in range(retries):
            try:
                response = requests.get(url=url, headers=HEADERS, cookies=cookies, timeout=timeout, verify=False)
                return response.content
            except Exception as e:
                logger.error(f"Failed to fetch data (attempt {attempt + 1}/{retries}): {e} url is: {url}")
                time.sleep(delay)
        logger.error(f"Max retries reached. Failed to fetch data. url is: {url}")
        return None

    def post(self, url: str, data: dict, cookies: Optional[dict] = None, retries: int = RETRY, delay: int = DELAY, timeout: int = TIMEOUT) -> Optional[requests.Response]:
        for attempt in range(retries):
            try:
                response = requests.post(url=url, data=data, headers=HEADERS, cookies=cookies, timeout=timeout, verify=False)
                return response
            except Exception as e:
                logger.error(f"Failed to post data (attempt {attempt + 1}/{retries}): {e} url is: {url}")
                time.sleep(delay)
        logger.error(f"Max retries reached. Failed to post data. url is: {url}")
        return None
