import miyuki.miyuki
import os

if __name__ == '__main__':

    proxy = "localhost:7890"

    os.environ["http_proxy"] = f"http://{proxy}"
    os.environ["https_proxy"] = f"http://{proxy}"

    miyuki.miyuki.download(movie_url="https://missav.com/en/skmj-551")