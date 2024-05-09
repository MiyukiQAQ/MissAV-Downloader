import requests
import re
import threading
import paramiko
import os
import shutil
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

video_m3u8_prefix = 'https://surrit.com/'
video_playlist_suffix = '/playlist.m3u8'

movie_save_path_root = 'movies'

hostname = "192.168.0.123"
username = "root"
password = ""


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
    html = requests.get(url=url, headers=headers).text

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
            response = requests.get(url=request_url, headers=headers, timeout=5).content
            return response
        except Exception as e:
            print(f"Failed to fetch data (attempt {retries + 1}/{max_retries}): {e} url is: {request_url}")
            retries += 1
            time.sleep(delay)
    print(f"Max retries reached. Failed to fetch data. url is: {request_url}")
    return None


def thread_task(start, end, uuid, movie_name):
    for i in range(start, end):
        url_tmp = 'https://surrit.com/' + uuid + '/' + resolution + '/' + 'video' + str(i) + '.jpeg'
        content = https_request_with_retry(url_tmp)
        if content is None: continue
        file_path = movie_save_path_root + '/' + movie_name + '/video' + str(i) + '.jpeg'
        with open(file_path, 'wb') as file:
            file.write(content)
            print('saved: ' + file_path)


def video_download(intervals, uuid, movie_name):
    thread_task_list = []

    for interval in intervals:
        start = interval[0]
        end = interval[1]
        thread = threading.Thread(target=thread_task, args=(start, end, uuid, movie_name))
        thread_task_list.append(thread)

    for thread in thread_task_list:
        thread.start()

    for thread in thread_task_list:
        thread.join()


def video_save(movie_name, video_offset_max):
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


if __name__ == '__main__':
    # List of movie URLs
    movie_urls = [
        'https://missav.com/dm13/en/orex-208',
        'https://missav.com/dm5/en/fone-066',
        'https://missav.com/dm19/en/cjod-371'
    ]

    for movie_url in movie_urls:
        movie_uuid = get_movie_uuid(movie_url)

        playlist_url = video_m3u8_prefix + movie_uuid + video_playlist_suffix

        playlist = requests.get(url=playlist_url, headers=headers).text

        # The last line records the highest resolution available for this video
        # For example: 1280x720/video.m3u8
        playlist_last_line = playlist.splitlines()[-1]

        resolution = playlist_last_line.split('/')[0]

        video_m3u8_url = video_m3u8_prefix + movie_uuid + '/' + playlist_last_line

        # video.m3u8 records all jpeg video units of the video
        video_m3u8 = requests.get(url=video_m3u8_url, headers=headers).text

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

        num_threads = os.cpu_count()
        intervals = split_integer_into_intervals(video_offset_max, num_threads)
        video_download(intervals, movie_uuid, movie_name)
        video_save(movie_name, video_offset_max)
        delete_directory(movie_name)
        # Transfer files to linux server
        # such as a stash movie lib
        scp_file(movie_name, hostname, username, password)
