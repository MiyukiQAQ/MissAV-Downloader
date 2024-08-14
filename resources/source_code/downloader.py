# import requests
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from curl_cffi import requests
import re
import threading
import paramiko
import os
import subprocess
import shutil
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

video_m3u8_prefix = 'https://surrit.com/'
video_playlist_suffix = '/playlist.m3u8'

movie_save_path_root = '../../movies'

ssh_server_user_info = {
    "hostname": "192.168.0.123",
    "username": "root",
    "password": "",
}

href_regex_movie_collection = r'<a class="text-secondary group-hover:text-primary" href="([^"]+)" alt="'
href_regex_public_playlist = r'<a href="([^"]+)" alt="'
href_regex_next_page = r'<a href="([^"]+)" rel="next"'

def get_public_playlist(playlist_url):
    movie_url_list = []
    print()
    print("Getting all video URLs")
    print()
    recursion_fill_movie_urls_by_page(playlist_url,movie_url_list)
    print("All video URLs have been obtained")
    print()
    return movie_url_list

def recursion_fill_movie_urls_by_page(playlist_url,movie_url_list):
    html_source = requests.get(url=playlist_url,headers=headers,verify=False).text
    movie_url_matches = re.findall(pattern=href_regex_public_playlist, string=html_source)
    temp_url_list = list(set(movie_url_matches))
    movie_url_list.extend(temp_url_list)
    print("page: " + playlist_url)
    print("movie url list: ")
    print(temp_url_list)
    print()
    next_page_matches = re.findall(pattern=href_regex_next_page, string=html_source)
    if (len(next_page_matches) == 1):
        next_page_url = next_page_matches[0]
        recursion_fill_movie_urls_by_page(next_page_url,movie_url_list)

def recursion_fill_movie_urls_by_page_with_cookie(url,movie_url_list,cookie):
    html_source = requests.get(url=url,cookies=cookie,headers=headers,verify=False).text
    movie_url_matches = re.findall(pattern=href_regex_movie_collection, string=html_source)
    movie_url_list.extend(list(set(movie_url_matches)))
    next_page_matches = re.findall(pattern=href_regex_next_page, string=html_source)
    if (len(next_page_matches) == 1):
        next_page_url = next_page_matches[0]
        recursion_fill_movie_urls_by_page_with_cookie(next_page_url,movie_url_list,cookie)

def login_get_cookie(missav_user_info):
    response = requests.post(url='https://missav.com/api/login', data=missav_user_info, headers=headers,verify=False)
    if response.status_code == 200:
        cookie_info = response.cookies.get_dict()
        print("cookie:")
        print(cookie_info)
    else:
        print("login failed, check your internet connection or your account info")
        exit(114514)

    return cookie_info


def get_movie_collections(cookie):
    movie_url_list = []
    url = 'https://missav.com/saved'
    recursion_fill_movie_urls_by_page_with_cookie(url,movie_url_list,cookie)
    return movie_url_list


def scp_file(movie_name, hostname, username, password):
    local_path = movie_save_path_root + '/' + movie_name + '.mp4'
    remote_path = "/home/workspace/data/stash/data/" + movie_name + '.mp4'

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"try scp {movie_name} to {remote_path}")

        ssh_client.connect(hostname=hostname, username=username, password=password)

        scp_client = ssh_client.open_sftp()
        scp_client.put(local_path, remote_path)
        scp_client.close()

        print(f"file scp success, remote path is: {remote_path}")
    except Exception as e:
        print(f"file scp error: {e}")
    finally:
        ssh_client.close()


def get_movie_uuid(url):
    html = requests.get(url=url, headers=headers,verify=False).text

    with open("movie.html", "w", encoding="UTF-8") as file:
        file.write(html)

    match = re.search(r'https:\\/\\/sixyik\.com\\/([^\\/]+)\\/seek\\/_0\.jpg', html)

    if match:
        print("match uuid success:", match.group(1))
        return match.group(1)
    else:
        print("match uuid failed.")


def create_folder_if_not_exists(folder_name):
    path = movie_save_path_root + '/' + folder_name
    if not os.path.exists(path):
        os.makedirs(path)


def delete_directory(movie_name):
    path = movie_save_path_root + '/' + movie_name
    try:
        shutil.rmtree(path)
        print(f"path '{path}' removed")
    except OSError as e:
        print(f"remove '{path}' error: {e.strerror}")


def split_integer_into_intervals(integer, n):
    interval_size = integer // n
    remainder = integer % n

    intervals = [(i * interval_size, (i + 1) * interval_size) for i in range(n)]

    intervals[-1] = (intervals[-1][0], intervals[-1][1] + remainder)

    return intervals


def https_request_with_retry(request_url, max_retries=5, delay=2):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url=request_url, headers=headers, timeout=5,verify=False).content
            return response
        except Exception as e:
            print(f"Failed to fetch data (attempt {retries + 1}/{max_retries}): {e} url is: {request_url}")
            retries += 1
            time.sleep(delay)
    print(f"Max retries reached. Failed to fetch data. url is: {request_url}")
    return None


def thread_task(start, end, uuid, resolution, movie_name):
    for i in range(start, end):
        url_tmp = 'https://surrit.com/' + uuid + '/' + resolution + '/' + 'video' + str(i) + '.jpeg'
        content = https_request_with_retry(url_tmp)
        if content is None: continue
        file_path = movie_save_path_root + '/' + movie_name + '/video' + str(i) + '.jpeg'
        with open(file_path, 'wb') as file:
            file.write(content)
            print('saved: ' + file_path)


def video_download_jpegs(intervals, uuid, resolution, movie_name):
    thread_task_list = []

    for interval in intervals:
        start = interval[0]
        end = interval[1]
        thread = threading.Thread(target=thread_task, args=(start, end, uuid, resolution, movie_name))
        thread_task_list.append(thread)

    for thread in thread_task_list:
        thread.start()

    for thread in thread_task_list:
        thread.join()


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
                print('not fond: ' + file_path)
                continue
            except Exception as e:
                print('exception: ' + str(e))
                continue

    print('save complete: ' + output_file_name)
    print(f'total files count: {video_offset_max + 1} , saved files count: {saved_count}')
    print('file integrity is {:.2%}'.format(saved_count / (video_offset_max + 1)))

def generate_input_txt(movie_name, video_offset_max):
    output_file_name = movie_save_path_root + '/' + movie_name + '.mp4'
    find_count = 0
    with open('input.txt', 'w') as input_txt:
        for i in range(video_offset_max + 1):
            file_path = movie_save_path_root + '/' + movie_name + '/video' + str(i) + '.jpeg'
            if os.path.exists(file_path):
                find_count = find_count + 1
                input_txt.write(f"file '{file_path}'\n")

    print('complete find jpegs for: ' + output_file_name)
    print(f'total files count: {video_offset_max + 1} , found files count: {find_count}')
    print('file integrity is {:.2%}'.format(find_count / (video_offset_max + 1)))
    print()

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
        subprocess.run(ffmpeg_command, check=True)
        print("ffmpeg execute complete")
    except subprocess.CalledProcessError as e:
        print(f"movie name: {movie_name}   ffmpeg execute failed: {e}")

def video_write_jpegs_to_mp4_by_ffmpeg(movie_name, video_offset_max):
    # make input.txt first
    generate_input_txt(movie_name, video_offset_max)
    generate_mp4_by_ffmpeg(movie_name)

def is_file_already_exists(movie_name):
    output_file_name = movie_save_path_root + '/' + movie_name + '.mp4'
    return os.path.exists(output_file_name)

def delete_all_subfolders(folder_path):
    if not os.path.exists(folder_path):
        return
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)

def get_movie_url_by_search(key):
    search_url = "https://missav.com/search/" + key
    search_regex = r'<a href="([^"]+)" alt="' + key + '">'
    html_source = requests.get(url=search_url,headers=headers,verify=False).text
    movie_url_matches = re.findall(pattern=search_regex, string=html_source)
    temp_url_list = list(set(movie_url_matches))
    if (len(temp_url_list) !=0 ):
        return temp_url_list[0]
    else:
        return None

def main(movie_url, download_action=True, write_action=True, delete_action=True, scp_action=True,ffmpeg_action=False, num_threads=os.cpu_count()):
    movie_uuid = get_movie_uuid(movie_url)
    if movie_uuid is None:
        return

    playlist_url = video_m3u8_prefix + movie_uuid + video_playlist_suffix

    playlist = requests.get(url=playlist_url, headers=headers,verify=False).text

    # The last line records the highest resolution available for this video
    # For example: 1280x720/video.m3u8
    playlist_last_line = playlist.splitlines()[-1]

    resolution = playlist_last_line.split('/')[0]

    video_m3u8_url = video_m3u8_prefix + movie_uuid + '/' + playlist_last_line

    # video.m3u8 records all jpeg video units of the video
    video_m3u8 = requests.get(url=video_m3u8_url, headers=headers,verify=False).text

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

    movie_name = movie_url.split('/')[-1]
    create_folder_if_not_exists(movie_name)

    intervals = split_integer_into_intervals(video_offset_max + 1, num_threads)

    if is_file_already_exists(movie_name):
        print(movie_name + " is already exists, skip download.")
        return
    
    if download_action:
        video_download_jpegs(intervals, movie_uuid, resolution, movie_name)
    if write_action:
        if ffmpeg_action:
            try:
                subprocess.run(['ffmpeg', '-version'], check=True)
            except subprocess.CalledProcessError as e:
                print("no ffmpeg found, downloader exist")
                exit(114514)

            video_write_jpegs_to_mp4_by_ffmpeg(movie_name, video_offset_max)
        else:
            video_write_jpegs_to_mp4(movie_name, video_offset_max)
    if delete_action:
        delete_directory(movie_name)
    # Transfer files to linux server
    # such as a stash movie lib
    if scp_action:
        scp_file(movie_name, ssh_server_user_info["hostname"], ssh_server_user_info["username"], ssh_server_user_info["password"])


if __name__ == '__main__':

    # type 1 : custom urls, change movie_urls into yourself

    # type 2 : login your account and download movies in your movie collections

    # type 3 : download from a public playlist url

    proxy_enable = False

    if proxy_enable:
        print("using proxy enabled")
        os.environ["http_proxy"] = "http://192.168.0.114:7890"
        os.environ["https_proxy"] = "http://192.168.0.114:7890"

    type = 1

    if type == 1:
        movie_urls = [
            'https://missav.com/dandy-917',
            'https://missav.com/sw-950'
        ]

    if type == 2:

        missav_user_info = {
            'email': 'xxxx@xxxx.com',
            'password': 'xxxx'
        }

        cookie = login_get_cookie(missav_user_info)
        movie_urls = get_movie_collections(cookie)
        print("your movie urls from your collection (total: " + str(len(movie_urls)) + " movies): ")
        for url in movie_urls:
            print(url)

    if type == 3:
        public_list_url = 'https://missav.com/playlists/ewzoukev'
        movie_urls = get_public_playlist(public_list_url)
        print("your movie urls from public playlist (total: " + str(len(movie_urls)) + " movies): ")
        for url in movie_urls:
            print(url)
        print()

    if type == 4:
        search_key = "sw-950"
        url = get_movie_url_by_search(search_key)
        if url is not None:
            print("Search success: " + url)
            movie_urls = [url]
        else:
            print("Search failed.")

    start_time = time.time()

    if movie_urls is None:
        print("movie_urls is None")
        print("exit")
        exit(114514)

    # befor download, clean the folder
    print("clean folder start")
    delete_all_subfolders(movie_save_path_root)
    print("clean folder end")


    for url in movie_urls:
        print("process url: " + url)
        main(url, scp_action=False)
        print("process url complete: " + url)

    # after download, clean the folder
    print("clean folder start")
    delete_all_subfolders(movie_save_path_root)
    print("clean folder end")

    end_time = time.time()
    duration = end_time - start_time
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    print("download time cost：{:02} h {:02} min {:02} s".format(int(hours), int(minutes), int(seconds)))
