"""
This script generates a word cloud from the article words. Uploads it to Imgur and returns back the url.
"""

import os
import random

import numpy as np
import requests
import wordcloud
from PIL import Image

import config

MASK_FILE = "./assets/cloud.png"
FONT_FILE = "./assets/sofiapro-light.otf"
IMAGE_PATH = "./temp.png"

COLORMAPS = ["spring", "summer", "autumn", "Wistia"]

mask = np.array(Image.open(MASK_FILE))


def generate_word_cloud(text):
    """Generates a word cloud and uploads it to Imgur.

    Parameters
    ----------
    text : str
        The text to be converted into a word cloud.

    Returns
    -------
    str
        The url generated from the Imgur API.
    """

    wc = wordcloud.WordCloud(background_color="#222222",
                             max_words=2000,
                             mask=mask,
                             contour_width=2,
                             colormap=random.choice(COLORMAPS),
                             font_path=FONT_FILE,
                             contour_color="white")

    wc.generate(text)
    wc.to_file(IMAGE_PATH)
    image_link = upload_image(IMAGE_PATH)
    os.remove(IMAGE_PATH)

    return image_link


def upload_image(image_path):
    """Uploads an image to Imgur and returns the permanent link url.

    Parameters
    ----------
    image_path : str
        The path of the file to be uploaded.

    Returns
    -------
    str
        The url generated from the Imgur API.
    """

    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": "Client-ID " + config.IMGUR_CLIENT_ID}
    files = {"image": open(IMAGE_PATH, "rb")}

    with requests.post(url, headers=headers, files=files) as response:

        # We extract the new link from the response.
        image_link = response.json()["data"]["link"]

        return image_link
