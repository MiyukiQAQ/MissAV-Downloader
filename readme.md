# MissAV-Downloader

MissAV-Downloader is a python crawler used to download videos from the MissAV website.

function type 1：

️➡️ You customize a list of movie URLs, and the downloader automatically downloads all the movies.

function type 2：

️️➡️ Automatically log in to your MissAV account, get all the videos you marked with a ❤️, and then automatically download them

function type 3：

️➡️ Download all videos in a public playlist (Maybe even any MissAV video collection page)

## Features

1. According to the number of CPU logical cores, multi-threaded fragment download.
2. By default, it supports downloading videos with the highest quality.
3. You can choose pure python implementation or ffmpeg implementation.
4. After the movie is downloaded, you can choose to send it to a server via SCP, which may be your stash server or the server of other private cinema applications, so that you can build your own movie library.
5. Support network proxy, if you are from an ancient oriental country, you may need a proxy.
6. It's very simple, you only need to know a little python to play with it.

## Installation

Use pip (or pip3) to install third-party libraries required by downloader.

```bash
pip install paramiko
pip install curl_cffi
pip install requests
```

## Usage
Modify the downloader.py source code and run it. This part of the code is at the bottom.

For example, you can change the type value to 2, and then modify ```missav_user_info``` and run it. This will log in to your account and automatically download the videos in your video collection. Or simply change ```movie_urls``` to download the video you want.



```python
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
```
---
How to download videos from public lists？

Please see the picture below ⬇️

Copy this url and paste it into variable ```public_list_url```, in type 3.

![public_playlist_url.png](public_playlist_url.png)
> [!TIP]
> Maybe even any MissAV video collection page, it could be an actor’s homepage, a label’s homepage, or a search result page, etc.
>
> The following URL is an example：
> https://missav.com/dm132/actresses/JULIA

---

If you want to use ffmpeg to synthesize the video.

You need to add a parameter when calling the main function.

This parameter is ```ffmpeg_action=True```

like this：
```python
    for url in movie_urls:
        print("process url: " + url)
        main(url, scp_action=False, ffmpeg_action=True)
        print("process url complete: " + url)
```

> [!WARNING]
> **But please note that this will only work if you have the ffmpeg program in your operating system and have configured the ffmpeg environment variables!**
