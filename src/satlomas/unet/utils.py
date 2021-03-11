from itertools import zip_longest

import keras
import skimage.transform
import cv2
import subprocess

__author__ = "Damián Silvani"
__copyright__ = "Dymaxion Labs"
__license__ = "apache-2.0"


def run_command(cmd):
    subprocess.run(cmd, shell=True, check=True)


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def load_model(model_path):
    return keras.models.load_model(model_path)


def resize(image, size):
    """Resize multiband image to an image of size (h, w)"""
    n_channels = image.shape[2]
    if n_channels >= 4:
        return skimage.transform.resize(
            image, size, mode="constant", preserve_range=True
        )
    else:
        return cv2.resize(image, size, interpolation=cv2.INTER_AREA)