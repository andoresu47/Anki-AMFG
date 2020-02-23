import os
import re
import requests
import urllib
from urllib.error import HTTPError

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 ' \
             'Safari/537.36 '
headers = {'User-Agent': USER_AGENT}


def get_image_urls(query_string):
    """
        Get all image urls from google image search
        Args:
            query_string: search term as of what is input to search box.
        Returns:
            (list): list of url for respective images.

        Inspired on: https://simply-python.com/2018/07/20/fast-download-images-from-google-image-search-with-python-requests-grequests/

    """

    query_string = query_string.replace(' ', '+')
    # Results sorted by relevance
    tgt_url = 'https://www.google.com.sg/search?q={}&tbm=isch&tbs=sbd:0'.format(query_string)

    r = requests.get(tgt_url, headers=headers)

    # urls = [n for n in re.findall('"([a-zA-Z0-9_.%/:-]+\.(?:jpg|jpeg|png))",', r.text)]
    decoded_text = bytes(r.text, "utf-8").decode("unicode_escape")

    urls = [n for n in re.findall('"(http[a-zA-Z0-9_.%/:&?=$,-]+)",', decoded_text)]

    return urls


def save_top_result(query_string, urls, thumbnail=True, directory="./"):
    top_result = None
    for url in urls:
        if thumbnail:
            if 'encrypted' in url:
                top_result = url
                try:
                    urllib.request.urlopen(top_result)
                except HTTPError:
                    continue
                break
        else:
            if 'encrypted' not in url and (
                    'image' in url or 'img' in url or 'jpg' in url or 'jpeg' in url or 'png' in url):
                top_result = url
                try:
                    urllib.request.urlopen(top_result)
                except HTTPError:
                    continue
                break

    if top_result is None:
        raise Exception("Links contain no images.")

    query_string = query_string.replace(' ', '_')
    path = os.path.join(directory, query_string + '.jpg')

    f = open(path, 'wb')
    f.write(urllib.request.urlopen(top_result).read())
    f.close()


def download_google_search_image(query_string, thumbnail=False, directory='./'):
    urls = get_image_urls(query_string)
    save_top_result(query_string, urls, thumbnail, directory)


if __name__ == "__main__":
    queries = ['växer upp', 'egentligen', 'en lagkamrat']
    for query in queries:
        download_google_search_image(query, False, "../data/")
