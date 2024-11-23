![MissAV-Downloader](https://socialify.git.ci/MiyukiQAQ/MissAV-Downloader/image?description=1&font=Inter&forks=1&issues=1&language=1&name=1&owner=1&pattern=Plus&pulls=1&stargazers=1&theme=Auto)

# Miyuki

⭐️ A tool for downloading videos from the "MissAV" website.

## ⚙️ Installation

To install Miyuki from the Python Package Index (PyPI) run:

```
pip install miyuki
```

To upgrade Miyuki from the Python Package Index (PyPI) run:

```
pip install --upgrade miyuki
```

## 📷 Snapshot

![snapshot.png](https://raw.githubusercontent.com/MiyukiQAQ/MissAV-Downloader/master/resources/readme_pics/snapshot.png)

## 📖 Instructions

```
[root@miyuki ~]# miyuki -h
usage: miyuki.py [-h] [-urls  [...]] [-auth  [...]] [-plist] [-limit] [-search] [-file] [-proxy] [-ffmpeg] [-cover] [-ffcover] [-noban] [-title]

A tool for downloading videos from the "MissAV" website.

Main Options:
Use the -urls   option to specify the video URLs to download.
Use the -auth   option to specify the username and password to download the videos collected by the account.
Use the -plist  option to specify the public playlist URL to download all videos in the list.
Use the -search option to search for movie by serial number and download it.
Use the -file   option to download all URLs in the file. ( Each line is a URL )

Additional Options:
Use the -limit   option to limit the number of downloads. (Only works with the -plist option.)
Use the -proxy   option to configure http proxy server ip and port.
Use the -ffmpeg  option to get the best video quality. ( Recommend! )
Use the -cover   option to save the cover when downloading the video
Use the -ffcover option to set the cover as the video preview (ffmpeg required)
Use the -noban   option to turn off the miyuki banner when downloading the video
Use the -title   option to use the full title as the movie file name

options:
  -h, --help     show this help message and exit
  -urls  [ ...]  Movie URLs, separate multiple URLs with spaces
  -auth  [ ...]  Username and password, separate with space
  -plist         Public playlist url
  -limit         Limit the number of downloads
  -search        Movie serial number
  -file          File path
  -proxy         HTTP(S) proxy
  -ffmpeg        Enable ffmpeg processing
  -cover         Download video cover
  -ffcover       Set cover as preview (ffmpeg required)
  -noban         Do not display the banner
  -title         Full title as file name

Examples:
  miyuki -plist "https://missav.com/search/JULIA?filters=uncensored-leak&sort=saved" -limit 50 -ffmpeg
  miyuki -plist "https://missav.com/search/JULIA?filters=individual&sort=views" -limit 20 -ffmpeg
  miyuki -plist "https://missav.com/dm132/actresses/JULIA" -limit 20 -ffmpeg -cover
  miyuki -plist "https://missav.com/playlists/ewzoukev" -ffmpeg -proxy localhost:7890
  miyuki -urls https://missav.com/sw-950 https://missav.com/dandy-917
  miyuki -urls https://missav.com/sw-950 -proxy localhost:7890
  miyuki -auth miyuki@gmail.com miyukiQAQ -ffmpeg
  miyuki -file /home/miyuki/url.txt -ffmpeg
  miyuki -search sw-950 -ffcover
```

## 🤫 The ```-plist``` option

- Use the -plist option to download movies from a playlist.
- This playlist can be a public playlist created by your own account, or any playlist displayed based on search results or tag filters.
- **You should wrap the playlist URL with " " when you use the -plist option.**

Command Examples:
- ```miyuki -plist "https://missav.com/search/JULIA?filters=uncensored-leak&sort=saved" -limit 50 -ffmpeg```
- ```miyuki -plist "https://missav.com/search/JULIA?filters=individual&sort=views" -limit 20 -ffmpeg```
- ```miyuki -plist "https://missav.com/dm132/actresses/JULIA" -limit 20 -ffmpeg```
- ```miyuki -plist "https://missav.com/playlists/ewzoukev" -limit 20 -ffmpeg```
- ```miyuki -plist "https://missav.com/dm444/en/labels/WANZ" -limit 20 -ffmpeg```
- ```miyuki -plist "https://missav.com/dm21/en/makers/Takara%20Visual" -limit 20 -ffmpeg```
- ```miyuki -plist "https://missav.com/dm1/en/genres/4K" -limit 20 -ffmpeg```

## ⚠️ Precautions

- If you are from an ancient oriental country, you will most likely need a proxy.
- Use ffmpeg to synthesize videos for the best experience.

## 👀 About FFmpeg

1. If you want miyuki to use ffmpeg to process the video, use the -ffmpeg option.
2. Please check whether the ffmpeg command is valid before using the -ffmpeg option. (e.g. ```ffmpeg -version```)
3. To install FFmpeg, please refer to https://ffmpeg.org/

## License

MIT

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=MiyukiQAQ/MissAV-Downloader&type=Date)](https://star-history.com/#MiyukiQAQ/MissAV-Downloader&Date)
