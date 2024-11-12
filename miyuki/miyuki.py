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
RECORD_FILE = 'miyuki_downloaded_urls.txt'
downloaded_urls = set()
movie_save_path_root = 'miyuki_movies_folder'
video_m3u8_prefix = 'https://surrit.com/'
video_playlist_suffix = '/playlist.m3u8'
href_regex_movie_collection = r'<a class="text-secondary group-hover:text-primary" href="([^"]+)" alt="'
href_regex_public_playlist = r'<a href="([^"]+)" alt="'
href_regex_next_page = r'<a href="([^"]+)" rel="next"'
match_uuid_pattern = r'm3u8\|([a-f0-9\|]+)\|com\|surrit\|https\|video'
# match_title_pattern = r'<h1 class="text-base lg:text-lg text-nord6">([^"]+)</h1>'
match_title_pattern = r'<title>([^"]+)</title>'
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


def https_request_with_retry(request_url, max_retries=5, delay=2):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url=request_url, headers=headers, timeout=5, verify=False).content
            return response
        except Exception as e:
            # logging.error(f"Failed to fetch data (attempt {retries + 1}/{max_retries}): {e} url is: {request_url}")
            retries += 1
            time.sleep(delay)
    # logging.error(f"Max retries reached. Failed to fetch data. url is: {request_url}")
    return None


def thread_task(start, end, uuid, resolution, movie_name, video_offset_max):
    for i in range(start, end):
        url_tmp = 'https://surrit.com/' + uuid + '/' + resolution + '/' + 'video' + str(i) + '.jpeg'
        content = https_request_with_retry(url_tmp)
        if content is None: continue
        file_path = movie_save_path_root + '/' + movie_name + '/video' + str(i) + '.jpeg'
        with open(file_path, 'wb') as file:
            file.write(content)
        display_progress_bar(video_offset_max + 1, counter)


def video_write_jpegs_to_mp4(movie_name, video_offset_max):
    output_file_name = movie_save_path_root + '/' + movie_name + '.mp4'
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


def generate_mp4_by_ffmpeg(movie_name):
    output_file_name = movie_save_path_root + '/' + movie_name + '.mp4'
    ffmpeg_command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'input.txt',
        '-c', 'copy',
        output_file_name
    ]
    try:
        subprocess.run(ffmpeg_command, check=True, stdout=subprocess.DEVNULL)
        logging.info("FFmpeg execution completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Movie name: {movie_name}, FFmpeg execution failed: {e}")


def generate_input_txt(movie_name, video_offset_max):
    output_file_name = movie_save_path_root + '/' + movie_name + '.mp4'
    find_count = 0
    with open('input.txt', 'w') as input_txt:
        for i in range(video_offset_max + 1):
            file_path = movie_save_path_root + '/' + movie_name + '/video' + str(i) + '.jpeg'
            if os.path.exists(file_path):
                find_count = find_count + 1
                input_txt.write(f"file '{file_path}'\n")

    print()
    logging.info('Complete save jpegs for: ' + output_file_name)
    logging.info(f'total files count: {video_offset_max + 1} , found files count: {find_count}')
    logging.info('file integrity is {:.2%}'.format(find_count / (video_offset_max + 1)))


def video_write_jpegs_to_mp4_by_ffmpeg(movie_name, video_offset_max):
    # make input.txt first
    generate_input_txt(movie_name, video_offset_max)
    generate_mp4_by_ffmpeg(movie_name)


def video_download_jpegs(intervals, uuid, resolution, movie_name, video_offset_max):
    thread_task_list = []

    for interval in intervals:
        start = interval[0]
        end = interval[1]
        thread = threading.Thread(target=thread_task, args=(start, end, uuid, resolution, movie_name, video_offset_max))
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

    with open("movie.html", "w", encoding="UTF-8") as file:
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
        if "uncensored-leak" in movie_name:
            result += " (Uncensored)"
        return result

    return None

def write_error_to_text_file(url, e):
    with open("miyuki_error.txt", "a", encoding="UTF-8") as file:
        file.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} - URL: {url} - Error: {e}\n")

def login_get_cookie(missav_user_info):
    response = requests.post(url='https://missav.com/api/login', data=missav_user_info, headers=headers, verify=False)
    if response.status_code == 200:
        cookie_info = response.cookies.get_dict()
        logging.info("cookie:")
        logging.info(cookie_info)
    else:
        logging.error("Login failed, check your network connection or account information.")
        exit(114514)

    return cookie_info

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

def download(movie_url, download_action=True, write_action=True, delete_action=True, ffmpeg_action=False,
             num_threads=os.cpu_count(), cover_action=True, title_action=True):

    movie_name = movie_url.split('/')[-1]

    if already_downloaded(movie_url):
        logging.info(movie_name + " already exists, skip downloading.")
        return

    movie_uuid, movie_html = get_movie_uuid(movie_url)
    if movie_uuid is None:
        return

    playlist_url = video_m3u8_prefix + movie_uuid + video_playlist_suffix

    playlist = requests.get(url=playlist_url, headers=headers, verify=False).text

    # The last line records the highest resolution available for this video
    # For example: 1280x720/video.m3u8
    playlist_last_line = find_last_non_empty_line(playlist)

    resolution = playlist_last_line.split('/')[0]

    video_m3u8_url = video_m3u8_prefix + movie_uuid + '/' + playlist_last_line

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
        video_download_jpegs(intervals, movie_uuid, resolution, movie_name, video_offset_max)
        counter.reset()

    if write_action:
        if ffmpeg_action:
            video_write_jpegs_to_mp4_by_ffmpeg(movie_name, video_offset_max)
        else:
            video_write_jpegs_to_mp4(movie_name, video_offset_max)

    with open(RECORD_FILE, 'a', encoding='utf-8') as file:
        file.write(movie_url + '\n')

    if movie_title is not None and title_action:
        os.rename(f"{movie_save_path_root}/{movie_name}.mp4", f"{movie_save_path_root}/{movie_title}.mp4")


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


def check_limit(limit):
    if limit is None:
        return True

    if limit.isdigit():
        return int(limit) > 0

    return False

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

def validate_args(args):
    urls = args.urls
    auth = args.auth
    plist = args.plist
    limit = args.limit
    ffmpeg = args.ffmpeg
    search = args.search
    file = args.file

    if not check_ffmpeg_command(ffmpeg):
        logging.error("FFmpeg command status error.")
        exit(magic_number)

    if not check_single_non_none(urls, auth, plist, search, file):
        logging.error("Among -urls, -auth, -search, -plist, and -file, exactly one option must be specified.")
        exit(magic_number)

    if not check_auth(auth):
        logging.error("The username and password entered are not in the correct format.")
        logging.error("Correct example: foo@gmail.com password")
        exit(magic_number)

    if not check_limit(limit):
        logging.error("The -limit option accepts only positive integers.")
        exit(magic_number)

    if not check_file(file):
        logging.error("The -file option accepts only a valid file path.")
        exit(magic_number)


def recursion_fill_movie_urls_by_page_with_cookie(url, movie_url_list, cookie):
    html_source = requests.get(url=url, cookies=cookie, headers=headers, verify=False).text
    movie_url_matches = re.findall(pattern=href_regex_movie_collection, string=html_source)
    temp_url_list = list(set(movie_url_matches))
    for movie_url in temp_url_list:
        movie_url_list.append(movie_url)
        logging.info(f"Movie {len(movie_url_list)} url: {movie_url}")
    next_page_matches = re.findall(pattern=href_regex_next_page, string=html_source)
    if (len(next_page_matches) == 1):
        next_page_url = next_page_matches[0].replace('&amp;', '&')
        recursion_fill_movie_urls_by_page_with_cookie(next_page_url, movie_url_list, cookie)


def recursion_fill_movie_urls_by_page(playlist_url, movie_url_list, limit):
    html_source = requests.get(url=playlist_url, headers=headers, verify=False).text
    movie_url_matches = re.findall(pattern=href_regex_public_playlist, string=html_source)
    temp_url_list = list(set(movie_url_matches))
    for movie_url in temp_url_list:
        movie_url_list.append(movie_url)
        logging.info(f"Movie {len(movie_url_list)} url: {movie_url}")
        if limit is not None and len(movie_url_list) >= int(limit):
            return
    next_page_matches = re.findall(pattern=href_regex_next_page, string=html_source)
    if (len(next_page_matches) == 1):
        next_page_url = next_page_matches[0].replace('&amp;', '&')
        recursion_fill_movie_urls_by_page(next_page_url, movie_url_list, limit)

def loop_fill_movie_urls_by_page(playlist_url, movie_url_list, limit):
    while playlist_url:
        html_source = requests.get(url=playlist_url, headers=headers, verify=False).text
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
    # recursion_fill_movie_urls_by_page(playlist_url, movie_url_list, limit)
    loop_fill_movie_urls_by_page(playlist_url, movie_url_list, limit)
    logging.info("All the video URLs have been successfully obtained.")
    return movie_url_list


def get_movie_collections(cookie):
    movie_url_list = []
    url = 'https://missav.com/saved'
    recursion_fill_movie_urls_by_page_with_cookie(url, movie_url_list, cookie)
    return movie_url_list


def get_movie_url_by_search(key):
    search_url = "https://missav.com/search/" + key
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
    search = args.search
    file = args.file
    title = args.title

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
            download(url, ffmpeg_action=ffmpeg, cover_action=cover, title_action=title)
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
                    'Use the -limit  option to limit the number of downloads. (Only works with the -plist option.)\n'
                    'Use the -proxy  option to configure http proxy server ip and port.\n'
                    'Use the -ffmpeg option to get the best video quality. ( Recommend! )\n'
                    'Use the -cover  option to save the cover when downloading the video\n'
                    'Use the -noban  option to turn off the miyuki banner when downloading the video\n'
                    'Use the -title  option to use the full title as the movie file name\n',


        epilog='Examples:\n'
               '  miyuki -plist "https://missav.com/search/JULIA?filters=uncensored-leak&sort=saved" -limit 50 -ffmpeg\n'
               '  miyuki -plist "https://missav.com/search/JULIA?filters=individual&sort=views" -limit 20 -ffmpeg\n'
               '  miyuki -plist https://missav.com/dm132/actresses/JULIA -limit 20 -ffmpeg -cover\n'
               '  miyuki -plist https://missav.com/playlists/ewzoukev -ffmpeg -proxy localhost:7890\n'
               '  miyuki -urls https://missav.com/sw-950 https://missav.com/dandy-917\n'
               '  miyuki -urls https://missav.com/sw-950 -proxy localhost:7890\n'
               '  miyuki -auth miyuki@gmail.com miyukiQAQ -ffmpeg\n'
               '  miyuki -file /home/miyuki/url.txt -ffmpeg\n'
               '  miyuki -search sw-950 -ffmpeg -cover\n',
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
    parser.add_argument('-noban', action='store_true', required=False, help='Do not display the banner')
    parser.add_argument('-title', action='store_true', required=False, help='Full title as file name')


    args = parser.parse_args()

    validate_args(args)

    if not args.noban:
        print(banner)

    execute_download(args)


if __name__ == "__main__":
    main()
