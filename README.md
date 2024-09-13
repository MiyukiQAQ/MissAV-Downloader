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
[root@miyuki ~]# miyuki --help
usage: miyuki.py [-h] [-urls  [...]] [-auth  [...]] [-plist] [-limit] [-search] [-proxy] [-ffmpeg]

A tool for downloading videos from the "MissAV" website.

Use the -urls   parameter to specify the video URLs to download.
Use the -auth   parameter to specify the username and password to download the videos collected by the account.
Use the -plist  parameter to specify the public playlist URL to download all videos in the list.
Use the -limit  parameter to limit the number of downloads. (Only works with the -plist parameter.)
Use the -search parameter to search for movie by serial number and download it.
Use the -proxy  parameter to configure http proxy server ip and port.
Use the -ffmpeg parameter to get the best video quality. ( Recommend! )

options:
  -h, --help     show this help message and exit
  -urls  [ ...]  Movie URLs, separate multiple URLs with spaces
  -auth  [ ...]  Username and password, separate with space
  -plist         Public playlist url
  -limit         Limit the number of downloads
  -search        Movie serial number
  -proxy         HTTP(S) proxy
  -ffmpeg        Enable ffmpeg processing

Examples:
  miyuki -plist "https://missav.com/search/JULIA?filters=uncensored-leak&sort=saved" -limit 50 -ffmpeg
  miyuki -plist "https://missav.com/search/JULIA?filters=individual&sort=views" -limit 20 -ffmpeg
  miyuki -plist https://missav.com/dm132/actresses/JULIA -limit 20 -ffmpeg
  miyuki -plist https://missav.com/playlists/ewzoukev -ffmpeg -proxy localhost:7890
  miyuki -urls https://missav.com/sw-950 https://missav.com/dandy-917
  miyuki -urls https://missav.com/sw-950 -proxy localhost:7890
  miyuki -auth miyuki@gmail.com miyukiQAQ -ffmpeg
  miyuki -search sw-950 -ffmpeg
```

## 🤫 The ```-plist``` parameter

Not only public playlists can be downloaded using the -plist parameter. Generally, any page that can be flipped can use the -plist parameter. But please note that if your URL contains an & symbol, you must wrap the URL with " " when using the -plist command.

For example, you can manually filter all the uncensored videos starring JULIA on the MissAV website and sort them by the number of favorites from most to least. The URL of the page you get is ```https://missav.com/search/JULIA?filters=uncensored-leak&sort=saved``` Since this URL contains an ampersand (&), in order for the command line to correctly treat this ampersand as part of the URL, you need to wrap the URL with a " " symbol. The final command is ```miyuki -plist "https://missav.com/search/JULIA?filters=uncensored-leak&sort=saved" -ffmpeg``` Of course, if you only want to download the first 100 videos, just use -limit 100.

If you are not sure whether you should wrap the URL with " ", the best way is to just choose to wrap the URL with " "

Command Examples:
- ```miyuki -plist "https://missav.com/search/JULIA?filters=uncensored-leak&sort=saved" -limit 50 -ffmpeg```
- ```miyuki -plist "https://missav.com/search/JULIA?filters=individual&sort=views" -limit 20 -ffmpeg```
- ```miyuki -plist https://missav.com/dm132/actresses/JULIA -limit 20 -ffmpeg```
- ```miyuki -plist https://missav.com/playlists/ewzoukev -limit 20 -ffmpeg```
- ```miyuki -plist https://missav.com/dm444/en/labels/WANZ -limit 20 -ffmpeg```
- ```miyuki -plist https://missav.com/dm21/en/makers/Takara%20Visual -limit 20 -ffmpeg```
- ```miyuki -plist https://missav.com/dm1/en/genres/4K -limit 20 -ffmpeg```

## ⚠️ Precautions

- If you are from an ancient oriental country, you will most likely need a proxy.
- Use ffmpeg to synthesize videos for the best experience.

## 👀 About FFmpeg

1. If you want miyuki to use ffmpeg to process the video, use the -ffmpeg parameter.
2. Please check whether the ffmpeg command is valid before using the -ffmpeg parameter. (e.g. ```ffmpeg -version```)
3. To install FFmpeg, please refer to https://ffmpeg.org/

## License

MIT
