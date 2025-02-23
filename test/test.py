import os

if __name__ == '__main__':

    proxy = "localhost:7890"

    os.environ["http_proxy"] = f"http://{proxy}"
    os.environ["https_proxy"] = f"http://{proxy}"

    resources.miyuki.download(movie_url="https://missav.com/ja/fc2-ppv-4597386", quality="700", download_action=False, ffmpeg_action=True, retry=10, delay=20, timeout=30, title_action=True)