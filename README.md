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

![snapshot.png](resources%2Freadme_pics%2Fsnapshot.png)

## 📖 Instructions

```
[root@miyuki ~]# miyuki --help
usage: miyuki [-h] [-urls  [...]] [-auth  [...]] [-plist] [-search] [-proxy]
              [-ffmpeg]

A tool for downloading videos from the "MissAV" website.

Use the -urls   parameter to specify the video URLs to download.
Use the -auth   parameter to specify the username and password to download the videos collected by the account.
Use the -plist  parameter to specify the public playlist URL to download all videos in the list.
Use the -search parameter to search for movie by serial number and download it.

optional arguments:
  -h, --help     show this help message and exit
  -urls  [ ...]  Movie URLs, separate multiple URLs with spaces
  -auth  [ ...]  Username and password, separate with space
  -plist         Public playlist url
  -search        Movie serial number
  -proxy         HTTP(S) proxy
  -ffmpeg        Enable ffmpeg processing

Examples:
  miyuki -plist https://missav.com/dm132/actresses/JULIA -ffmpeg -proxy localhost:7890
  miyuki -plist https://missav.com/playlists/ewzoukev -ffmpeg
  miyuki -auth miyuki@gmail.com miyukiQAQ -ffmpeg -proxy localhost:7890
  miyuki -urls https://missav.com/sw-950 https://missav.com/dandy-917
  miyuki -urls https://missav.com/sw-950 -proxy localhost:7890
  miyuki -urls https://missav.com/sw-950 -ffmpeg
  miyuki -urls https://missav.com/sw-950
  miyuki -search sw-950
```

## ⚠️ Precautions

- If you are from an ancient oriental country, you will most likely need a proxy.
- Use ffmpeg to synthesize videos for the best experience.

## 👀 About FFmpeg

1. If you want miyuki to use ffmpeg to process the video, use the -ffmpeg parameter.
2. Please check whether the ffmpeg command is valid before using the -ffmpeg parameter. (e.g. ```ffmpeg -version```)
3. To install FFmpeg, please refer to https://ffmpeg.org/

## License

MIT