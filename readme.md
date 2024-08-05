Before running the downloader, you need to install the dependent libraries using pip or pip3：

pip install curl_cffi 

pip install paramiko 

pip install requests 

This readme is too ugly. I will make a more beautiful one later.
------------------------------------------------------------------------------------------------

how to run this：

I recommend running the downloader.py directly in the PyCharm development environment. 

When you copy the movie URL from MissAV, it is best to use the English version of the MissAV page

You need Python 3

type 1 : custom urls, change movie_urls into yourself

type 2 : login your account automatically and download movies from your movie collections

type 3 : download from a public playlist url
![public_playlist_url.png](public_playlist_url.png)

Due to the m3u8 fragment download, the more CPU logical threads there are, the faster the download speed

ps: 

1. If you are from an ancient eastern country, then you may need to use a network proxy
