import argparse
import logging
import os
import re
import subprocess
import shutil
import threading
import time
import sys
from curl_cffi import requests

logging.basicConfig(level=logging.DEBUG,
                    format='Miyuki - %(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

magic_number = 114514
RECORD_FILE = 'downloaded_urls_miyuki.txt'
FFMPEG_INPUT_FILE = 'ffmpeg_input_miyuki.txt'
ERROR_RECORD_FILE = 'error_records_miyuki.txt'
TMP_HTML_FILE = 'tmp_movie_miyuki.html'
downloaded_urls = set()
movie_save_path_root = 'movies_folder_miyuki'
video_m3u8_prefix = 'https://surrit.com/'
video_playlist_suffix = '/playlist.m3u8'
href_regex_movie_collection = r'<a class="text-secondary group-hover:text-primary" href="([^"]+)" alt="'
href_regex_public_playlist = r'<a href="([^"]+)" alt="'
href_regex_next_page = r'<a href="([^"]+)" rel="next"'
match_uuid_pattern = r'm3u8\|([a-f0-9\|]+)\|com\|surrit\|https\|video'
# match_title_pattern = r'<h1 class="text-base lg:text-lg text-nord6">([^"]+)</h1>'
match_title_pattern = r'<title>([^"]+)</title>'
RESOLUTION_PATTERN = r'RESOLUTION=(\d+)x(\d+)'
RETRY = 5
DELAY = 2
TIMEOUT = 10
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

banner = """
 ██████   ██████  ███                        █████       ███ 
░░██████ ██████  ░░░                        ░░███       ░░░  
 ░███░█████░███  ████  █████ ████ █████ ████ ░███ █████ ████ 
 ░███░░███ ░███ ░░███ ░░███ ░███ ░░███ ░███  ░███░░███ ░░███ 
 ░███ ░░░  ░███  ░███  ░███ ░███  ░███ ░███  ░██████░   ░███ 
 ░███      ░███  ░███  ░███ ░███  ░███ ░███  ░███░░███  ░███ 
 █████     █████ █████ ░░███████  ░░████████ ████ █████ █████
░░░░░     ░░░░░ ░░░░░   ░░░░░███   ░░░░░░░░ ░░░░ ░░░░░ ░░░░░ 
                        ███ ░███                             
                       ░░██████                              
                        ░░░░░░                               
"""


def display_progress_bar(max_value, counter):
    bar_length = 50
    current_value = counter.incrementAndGet()
    progress = current_value / max_value
    block = int(round(bar_length * progress))
    text = f"\rProgress: [{'#' * block + '-' * (bar_length - block)}] {current_value}/{max_value}"
    sys.stdout.write(text)
    sys.stdout.flush()


class ThreadSafeCounter:
    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()

    def incrementAndGet(self):
        with self._lock:
            self._count += 1
            return self._count

    def reset(self):
        with self._lock:
            self._count = 0

    def get_count(self):
        with self._lock:
            return self._count


counter = ThreadSafeCounter()


def https_request_with_retry(request_url, retry, delay, timeout):
    inner_retry = RETRY
    inner_delay = DELAY
    inner_timeout = TIMEOUT
    if retry is not None:
        inner_retry = int(retry)
    if delay is not None:
        inner_delay = int(delay)
    if timeout is not None:
        inner_timeout = int(timeout)
    retries = 0
    while retries < inner_retry:
        try:
            response = requests.get(url=request_url, headers=headers, timeout=inner_timeout, verify=False).content
            return response
        except Exception as e:
            # logging.error(f"Failed to fetch data (attempt {retries + 1}/{max_retries}): {e} url is: {request_url}")
            retries += 1
            time.sleep(inner_delay)
    # logging.error(f"Max retries reached. Failed to fetch data. url is: {request_url}")
    return None


def thread_task(start, end, uuid, resolution, movie_name, video_offset_max, retry, delay, timeout):
    for i in range(start, end):
        url_tmp = 'https://surrit.com/' + uuid + '/' + resolution + '/' + 'video' + str(i) + '.jpeg'
        content = https_request_with_retry(url_tmp, retry, delay, timeout)
        if content is None: continue
        file_path = movie_save_path_root + '/' + movie_name + '/video' + str(i) + '.jpeg'
        with open(file_path, 'wb') as file:
            file.write(content)
        display_progress_bar(video_offset_max + 1, counter)


def video_write_jpegs_to_mp4(movie_name, video_offset_max, final_file_name):
    movie_file_name = final_file_name + '.mp4'
    output_file_name = movie_save_path_root + '/' + movie_file_name
    saved_count = 0
    with open(output_file_name, 'wb') as outfile:
        for i in range(video_offset_max + 1):
            file_path = movie_save_path_root + '/' + movie_name + '/video' + str(i) + '.jpeg'
            try:
                with open(file_path, 'rb') as infile:
                    outfile.write(infile.read())
                    saved_count = saved_count + 1
                    print('write: ' + file_path)
            except FileNotFoundError:
                print('file not found: ' + file_path)
                continue
            except Exception as e:
                print('exception: ' + str(e))
                continue

    logging.info('Save Completed: ' + output_file_name)
    logging.info(f'Total number of files: {video_offset_max + 1} , number of files saved: {saved_count}')
    logging.info('The file integrity is {:.2%}'.format(saved_count / (video_offset_max + 1)))


def generate_mp4_by_ffmpeg(movie_name, final_file_name, cover_as_preview):
    movie_file_name = final_file_name + '.mp4'
    output_file_name = movie_save_path_root + '/' + movie_file_name
    cover_file_name = movie_save_path_root + '/' + movie_name + '-cover.jpg'
    if cover_as_preview and os.path.exists(cover_file_name):
        # ffmpeg -i video.mp4 -i cover.jpg -map 1 -map 0 -c copy -disposition:0 attached_pic output.mp4
        ffmpeg_command = [
            'ffmpeg',
            '-loglevel', 'error',
            '-f', 'concat',
            '-safe', '0',
            '-i', FFMPEG_INPUT_FILE,
            '-i', cover_file_name,
            '-map', '0',
            '-map', '1',
            '-c', 'copy',
            '-disposition:v:1', 'attached_pic',
            output_file_name
        ]

    else:
        ffmpeg_command = [
            'ffmpeg',
            '-loglevel', 'error',
            '-f', 'concat',
            '-safe', '0',
            '-i', FFMPEG_INPUT_FILE,
            '-c', 'copy',
            output_file_name
        ]


    try:
        logging.info("FFmpeg executing...")
        subprocess.run(ffmpeg_command, check=True, stdout=subprocess.DEVNULL)
        logging.info("FFmpeg execution completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Movie name: {movie_name}, FFmpeg execution failed: {e}")
        raise e

def generate_input_txt(movie_name, video_offset_max):
    output_file_name = movie_save_path_root + '/' + movie_name + '.mp4'
    find_count = 0
    with open(FFMPEG_INPUT_FILE, 'w') as input_txt:
        for i in range(video_offset_max + 1):
            file_path = movie_save_path_root + '/' + movie_name + '/video' + str(i) + '.jpeg'
            if os.path.exists(file_path):
                find_count = find_count + 1
                input_txt.write(f"file '{file_path}'\n")

    print()
    total_files = video_offset_max + 1
    downloaded_files = find_count
    completion_rate = '{:.2%}'.format(downloaded_files / (total_files))
    logging.info(f'Total files : {total_files} , downloaded files : {downloaded_files} , completion rate : {completion_rate}')


def video_write_jpegs_to_mp4_by_ffmpeg(movie_name, video_offset_max, cover_as_preview, final_file_name):
    # make input.txt first
    generate_input_txt(movie_name, video_offset_max)
    generate_mp4_by_ffmpeg(movie_name, final_file_name, cover_as_preview)


def video_download_jpegs(intervals, uuid, resolution, movie_name, video_offset_max, retry, delay, timeout):
    thread_task_list = []

    for interval in intervals:
        start = interval[0]
        end = interval[1]
        thread = threading.Thread(target=thread_task, args=(start, end, uuid, resolution, movie_name, video_offset_max, retry, delay, timeout))
        thread_task_list.append(thread)

    for thread in thread_task_list:
        thread.start()

    for thread in thread_task_list:
        thread.join()


def split_integer_into_intervals(integer, n):
    interval_size = integer // n
    remainder = integer % n

    intervals = [(i * interval_size, (i + 1) * interval_size) for i in range(n)]

    intervals[-1] = (intervals[-1][0], intervals[-1][1] + remainder)

    return intervals


def create_root_folder_if_not_exists(folder_name):
    path = movie_save_path_root + '/' + folder_name
    if not os.path.exists(path):
        os.makedirs(path)


def get_movie_uuid(url):
    html = requests.get(url=url, headers=headers, verify=False).text

    with open(TMP_HTML_FILE, "w", encoding="UTF-8") as file:
        file.write(html)

    match = re.search(match_uuid_pattern, html)

    if match:
        result = match.group(1)
        resule_str_list = result.split("|")
        uuid = "-".join(resule_str_list[::-1])
        logging.info("Matching uuid successfully: " + uuid)
        return uuid, html
    else:
        logging.error("Failed to match uuid.")

def get_movie_title(movie_html, movie_name):

    match = re.search(match_title_pattern, movie_html)

    if match:
        result = match.group(1)
        result = result.replace("&#039;", "'")
        # if "uncensored-leak" in movie_name:
        #     result += "[Uncensored]"
        result = result.replace('/', '_')
        result = result.replace('\\', '_')
        return result

    return None

def write_error_to_text_file(url, e):
    with open(ERROR_RECORD_FILE, "a", encoding="UTF-8") as file:
        file.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} - URL: {url} - Error: {e}\n")

def login_get_cookie(missav_user_info):
    response = requests.post(url='https://missav.ai/api/login', data=missav_user_info, headers=headers, verify=False)
    if response.status_code == 200:
        cookie_info = response.cookies.get_dict()
        if "user_uuid" in cookie_info:
            logging.info("User uuid: " + cookie_info["user_uuid"])
            return cookie_info

    logging.error("Login failed, check your network connection or account information.")
    exit(magic_number)

def find_last_non_empty_line(text):
    lines = text.splitlines()
    for line in reversed(lines):
        if line.strip():
            return line
    raise Exception("Failed to find the last non-empty line in m3u8 playlist.")

def already_downloaded(url):
    if os.path.exists(RECORD_FILE):
        with open(RECORD_FILE, 'r', encoding='utf-8') as file:
            for line in file:
                downloaded_urls.add(line.strip())
    return url in downloaded_urls


def find_closest(arr, target):

    closest_value = arr[0]
    min_diff = abs(arr[0] - target)

    for num in arr:
        current_diff = abs(num - target)
        if current_diff < min_diff:
            min_diff = current_diff
            closest_value = num

    return str(closest_value)


def get_final_quality_and_resolution(playlist, quality : str):
    try:
        matches = re.findall(pattern=RESOLUTION_PATTERN, string=playlist)
        quality_map = {}
        quality_list = []
        m3u8_suffix = '/video.m3u8'
        for match in matches:
            quality_map[match[1]] = match[0]
            quality_list.append(match[1])

        if quality is None:
            return quality_list[-1] + 'p', find_last_non_empty_line(playlist)
        else:
            closest_resolution = find_closest(list(map(int, quality_list)), int(quality))
            url_type_x = quality_map[closest_resolution] + 'x' + closest_resolution + m3u8_suffix
            url_type_p = closest_resolution + 'p' + m3u8_suffix
            if url_type_x in playlist:
                return closest_resolution + 'p', url_type_x
            elif url_type_p in playlist:
                return closest_resolution + 'p', url_type_p
            else:
                return quality_list[-1] + 'p', find_last_non_empty_line(playlist)
    except Exception as e:
        resolution_url = find_last_non_empty_line(playlist)
        final_quality = resolution_url.split('/')[0]
        return final_quality, resolution_url



def download(movie_url, download_action=True, write_action=True, ffmpeg_action=False,
             num_threads=os.cpu_count(), cover_action=True, title_action=False, cover_as_preview=False, quality=None , retry=None, delay=None, timeout=None):

    movie_name = movie_url.split('/')[-1]

    if already_downloaded(movie_url):
        logging.info(movie_name + " already exists, skip downloading.")
        return

    movie_uuid, movie_html = get_movie_uuid(movie_url)
    if movie_uuid is None:
        return

    playlist_url = video_m3u8_prefix + movie_uuid + video_playlist_suffix

    playlist = requests.get(url=playlist_url, headers=headers, verify=False).text

    final_quality, resolution_url = get_final_quality_and_resolution(playlist, quality)

    final_file_name = movie_name + '_' + final_quality

    resolution = resolution_url.split('/')[0]

    video_m3u8_url = video_m3u8_prefix + movie_uuid + '/' + resolution_url

    # video.m3u8 records all jpeg video units of the video
    video_m3u8 = requests.get(url=video_m3u8_url, headers=headers, verify=False).text

    # In the penultimate line of video.m3u8, find the maximum jpeg video unit number of the video
    video_offset_max_str = video_m3u8.splitlines()[-2]
    # For example:
    # video1772.jpeg
    # #EXTINF:5.000000,
    # video1773.jpeg
    # #EXTINF:2.500000,
    # video1774.jpeg
    # #EXTINF:2.250000,
    # video1775.jpeg
    # #EXT-X-ENDLIST
    video_offset_max = int(re.search(r'(\d+)', video_offset_max_str).group(0))

    create_root_folder_if_not_exists(movie_name)

    intervals = split_integer_into_intervals(video_offset_max + 1, num_threads)

    movie_title = get_movie_title(movie_html, movie_name)

    if cover_action:
        try:
            cover_pic_url = f"https://fivetiu.com/{movie_name}/cover-n.jpg"
            cover_pic = requests.get(url=cover_pic_url, headers=headers, verify=False).content
            with open(movie_save_path_root + '/' + movie_name + '-cover.jpg', 'wb') as file:
                file.write(cover_pic)
        except Exception as e:
            logging.error(f"Movie name : {movie_name}, failed to download the cover: {e}")

    if download_action:
        counter.reset()
        video_download_jpegs(intervals, movie_uuid, resolution, movie_name, video_offset_max, retry, delay, timeout)
        counter.reset()

    if write_action:
        if ffmpeg_action:
            video_write_jpegs_to_mp4_by_ffmpeg(movie_name, video_offset_max, cover_as_preview, final_file_name)
        else:
            video_write_jpegs_to_mp4(movie_name, video_offset_max, final_file_name)

    with open(RECORD_FILE, 'a', encoding='utf-8') as file:
        file.write(movie_url + '\n')

    if movie_title is not None and title_action:
        os.rename(f"{movie_save_path_root}/{final_file_name}.mp4", f"{movie_save_path_root}/{movie_title}.mp4")


def delete_all_subfolders(folder_path):
    if not os.path.exists(folder_path):
        return
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)


def check_single_non_none(param1, param2, param3, param4, param5):
    non_none_count = sum(param is not None for param in [param1, param2, param3, param4, param5])
    return non_none_count == 1


def check_ffmpeg_command(ffmpeg):
    if ffmpeg:
        try:
            subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError as e:
            return False
    else:
        return True


def check_auth(auth):
    if auth is None:
        return True

    if len(auth) != 2:
        return False
    else:
        return True

def check_file(file_path):
    if file_path is None:
        return True

    if not os.path.isfile(file_path):
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file.read()
    except (UnicodeDecodeError, IOError):
        return False

    return os.path.getsize(file_path) > 0

def check_positive_integer(limit):
    if limit is None:
        return True

    if limit.isdigit():
        return int(limit) > 0

    return False

def validate_args(args):
    urls = args.urls
    auth = args.auth
    plist = args.plist
    limit = args.limit
    ffmpeg = args.ffmpeg
    ffcover = args.ffcover
    search = args.search
    file = args.file
    quality = args.quality
    retry = args.retry
    delay = args.delay
    timeout = args.timeout

    if not check_ffmpeg_command(ffmpeg):
        logging.error("FFmpeg command status error.")
        exit(magic_number)

    if not check_ffmpeg_command(ffcover):
        logging.error("FFmpeg command status error.")
        exit(magic_number)

    if not check_single_non_none(urls, auth, plist, search, file):
        logging.error("Among -urls, -auth, -search, -plist, and -file, exactly one option must be specified.")
        exit(magic_number)

    if not check_auth(auth):
        logging.error("The username and password entered are not in the correct format.")
        logging.error("Correct example: foo@gmail.com password")
        exit(magic_number)

    if not check_positive_integer(limit):
        logging.error("The -limit option accepts only positive integers.")
        exit(magic_number)

    if not check_file(file):
        logging.error("The -file option accepts only a valid file path.")
        exit(magic_number)

    if not check_positive_integer(quality):
        logging.error("The -quality option accepts only positive integers.")
        exit(magic_number)

    if not check_positive_integer(retry):
        logging.error("The -retry option accepts only positive integers.")
        exit(magic_number)

    if not check_positive_integer(delay):
        logging.error("The -delay option accepts only positive integers.")
        exit(magic_number)

    if not check_positive_integer(timeout):
        logging.error("The -timeout option accepts only positive integers.")
        exit(magic_number)

def loop_fill_movie_urls_by_page(playlist_url, movie_url_list, limit, cookie):
    while playlist_url:
        html_source = requests.get(url=playlist_url, headers=headers, verify=False, cookies=cookie).text
        movie_url_matches = re.findall(pattern=href_regex_public_playlist, string=html_source)
        temp_url_list = list(set(movie_url_matches))
        for movie_url in temp_url_list:
            movie_url_list.append(movie_url)
            logging.info(f"Movie {len(movie_url_list)} url: {movie_url}")
            if limit is not None and len(movie_url_list) >= int(limit):
                return
        next_page_matches = re.findall(pattern=href_regex_next_page, string=html_source)
        if len(next_page_matches) == 1:
            playlist_url = next_page_matches[0].replace('&amp;', '&')
        else:
            break

def get_public_playlist(playlist_url, limit):
    movie_url_list = []
    logging.info("Getting the URLs of all movies.")
    loop_fill_movie_urls_by_page(playlist_url=playlist_url, movie_url_list=movie_url_list, limit=limit, cookie=None)
    logging.info("All the video URLs have been successfully obtained.")
    return movie_url_list


def get_movie_collections(cookie):
    movie_url_list = []
    url = 'https://missav.ai/saved'
    loop_fill_movie_urls_by_page(playlist_url=url, movie_url_list=movie_url_list, limit=None, cookie=cookie)
    logging.info("All the video URLs have been successfully obtained.")
    return movie_url_list


def get_movie_url_by_search(key):
    search_url = "https://missav.ai/search/" + key
    search_regex = r'<a href="([^"]+)" alt="' + key + '" >'
    html_source = requests.get(url=search_url, headers=headers, verify=False).text
    movie_url_matches = re.findall(pattern=search_regex, string=html_source)
    temp_url_list = list(set(movie_url_matches))
    if (len(temp_url_list) != 0):
        return temp_url_list[0]
    else:
        return None

def get_urls_from_file(file):
    with open(file, 'r', encoding='utf-8') as file:
        urls = file.readlines()
    urls = [url.strip() for url in urls]
    return urls

def execute_download(args):
    urls = args.urls
    auth = args.auth
    plist = args.plist
    limit = args.limit
    proxy = args.proxy
    ffmpeg = args.ffmpeg
    cover = args.cover
    ffcover = args.ffcover
    search = args.search
    file = args.file
    title = args.title
    quality = args.quality
    retry = args.retry
    delay = args.delay
    timeout = args.timeout

    if ffcover:
        ffmpeg = True
        cover = True

    if proxy is not None:
        logging.info("Network proxy enabled.")
        os.environ["http_proxy"] = f"http://{proxy}"
        os.environ["https_proxy"] = f"http://{proxy}"

    movie_urls = []

    if urls is not None:
        movie_urls = urls

    if auth is not None:
        username = auth[0]
        password = auth[1]
        cookie = login_get_cookie({'email': username, 'password': password})
        movie_urls = get_movie_collections(cookie)
        logging.info("The URLs of all the videos you have favorited (total: " + str(len(movie_urls)) + " movies): ")
        for url in movie_urls:
            logging.info(url)

    if plist is not None:
        movie_urls = get_public_playlist(plist, limit)
        logging.info("The URLs of all videos in this playlist (total: " + str(len(movie_urls)) + " movies): ")
        for url in movie_urls:
            logging.info(url)

    if search is not None:
        url = get_movie_url_by_search(search)
        if url is not None:
            logging.info("Search " + search + " successfully: " + url)
            movie_urls.append(url)
        else:
            logging.error("Search failed, key: " + search)
            exit(magic_number)

    if file is not None:
        movie_urls = get_urls_from_file(file)
        logging.info("The URLs of all videos in the file (total: " + str(len(movie_urls)) + " movies): ")
        for url in movie_urls:
            logging.info(url)


    if (len(movie_urls) == 0):
        logging.error("No urls found.")
        exit(magic_number)

    for url in movie_urls:
        delete_all_subfolders(movie_save_path_root)
        try:
            logging.info("Processing URL: " + url)
            download(url, ffmpeg_action=ffmpeg, cover_action=cover, title_action=title, cover_as_preview=ffcover, quality=quality, retry=retry, delay=delay, timeout=timeout)
            logging.info("Processing URL Complete: " + url)
        except Exception as e:
            logging.error(f"Failed to download the movie: {url}, error: {e}")
            write_error_to_text_file(url, e)
        delete_all_subfolders(movie_save_path_root)


def main():
    parser = argparse.ArgumentParser(
        description='A tool for downloading videos from the "MissAV" website.\n'
                    '\n'
                    'Main Options:\n'
                    'Use the -urls   option to specify the video URLs to download.\n'
                    'Use the -auth   option to specify the username and password to download the videos collected by the account.\n'
                    'Use the -plist  option to specify the public playlist URL to download all videos in the list.\n'
                    'Use the -search option to search for movie by serial number and download it.\n'
                    'Use the -file   option to download all URLs in the file. ( Each line is a URL )\n'
                    '\n'
                    'Additional Options:\n'
                    'Use the -limit   option to limit the number of downloads. (Only works with the -plist option.)\n'
                    'Use the -proxy   option to configure http proxy server ip and port.\n'
                    'Use the -ffmpeg  option to get the best video quality. ( Recommend! )\n'
                    'Use the -cover   option to save the cover when downloading the video\n'
                    'Use the -ffcover option to set the cover as the video preview (ffmpeg required)\n'
                    'Use the -noban   option to turn off the miyuki banner when downloading the video\n'
                    'Use the -title   option to use the full title as the movie file name\n'
                    'Use the -quality option to specify the movie resolution (360, 480, 720, 1080...)\n'
                    'Use the -retry   option to specify the number of retries for downloading segments\n'
                    'Use the -delay   option to specify the delay before retry ( seconds )\n'
                    'Use the -timeout option to specify the timeout for segment download ( seconds )\n',


        epilog='Examples:\n'
               '  miyuki -plist "https://missav.ai/search/JULIA?filters=uncensored-leak&sort=saved" -limit 50 -ffmpeg\n'
               '  miyuki -plist "https://missav.ai/search/JULIA?filters=individual&sort=views" -limit 20 -ffmpeg\n'
               '  miyuki -plist "https://missav.ai/dm132/actresses/JULIA" -limit 20 -ffmpeg -cover\n'
               '  miyuki -plist "https://missav.ai/playlists/ewzoukev" -ffmpeg -proxy localhost:7890\n'
               '  miyuki -urls https://missav.ai/sw-950 https://missav.ai/dandy-917\n'
               '  miyuki -urls https://missav.ai/sw-950 -proxy localhost:7890\n'
               '  miyuki -auth miyuki@gmail.com miyukiQAQ -ffmpeg\n'
               '  miyuki -file /home/miyuki/url.txt -ffmpeg\n'
               '  miyuki -search sw-950 -ffcover\n',
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument('-urls', nargs='+', required=False, metavar='',help='Movie URLs, separate multiple URLs with spaces')
    parser.add_argument('-auth', nargs='+', required=False, metavar='',help='Username and password, separate with space')
    parser.add_argument('-plist', type=str, required=False, metavar='', help='Public playlist url')
    parser.add_argument('-limit', type=str, required=False, metavar='', help='Limit the number of downloads')
    parser.add_argument('-search', type=str, required=False, metavar='', help='Movie serial number')
    parser.add_argument('-file', type=str, required=False, metavar='', help='File path')
    parser.add_argument('-proxy', type=str, required=False, metavar='', help='HTTP(S) proxy')
    parser.add_argument('-ffmpeg', action='store_true', required=False, help='Enable ffmpeg processing')
    parser.add_argument('-cover', action='store_true', required=False, help='Download video cover')
    parser.add_argument('-ffcover', action='store_true', required=False, help='Set cover as preview (ffmpeg required)')
    parser.add_argument('-noban', action='store_true', required=False, help='Do not display the banner')
    parser.add_argument('-title', action='store_true', required=False, help='Full title as file name')
    parser.add_argument('-quality', type=str, required=False, metavar='', help='Specify the movie resolution')
    parser.add_argument('-retry', type=str, required=False, metavar='', help='Number of retries for downloading segments')
    parser.add_argument('-delay', type=str, required=False, metavar='', help='Delay in seconds before retry')
    parser.add_argument('-timeout', type=str, required=False, metavar='', help='Timeout in seconds for segment download')


    args = parser.parse_args()

    validate_args(args)

    if not args.noban:
        print(banner)

    execute_download(args)


if __name__ == "__main__":
    main()
