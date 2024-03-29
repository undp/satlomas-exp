import json
import logging
import math
import os
from functools import partial

import numpy as np
import pyproj
import rasterio
from rasterio.windows import Window
from shapely.geometry import mapping
from shapely.ops import transform
from skimage import exposure
from tqdm import tqdm

__author__ = "Damián Silvani"
__copyright__ = "Dymaxion Labs"
__license__ = "apache-2.0"

_logger = logging.getLogger(__name__)


def reproject_shape(shp, from_crs, to_crs):
    project = partial(pyproj.transform, pyproj.Proj(from_crs), pyproj.Proj(to_crs))
    return transform(project, shp)


def sliding_windows(size, step_size, width, height, whole=False):
    """Slide a window of +size+ by moving it +step_size+ pixels"""
    w, h = size
    sw, sh = step_size
    end_i = height - h if whole else height
    end_j = width - w if whole else width
    for pos_i, i in enumerate(range(0, end_i, sh)):
        for pos_j, j in enumerate(range(0, end_j, sw)):
            real_w = w if whole else min(w, abs(width - j))
            real_h = h if whole else min(h, abs(height - i))
            yield Window(j, i, real_w, real_h), (pos_i, pos_j)


def rescale_intensity(image, rescale_mode, rescale_range):
    """
    Calculate percentiles from a range cut and
    rescale intensity of image to byte range

    Parameters
    ----------
    image : numpy.ndarray
        image array
    rescale_mode : str
        rescaling mode, either 'percentiles' or 'values'
    rescale_range : Tuple[number, number]
        input range for rescaling

    Returns
    -------
    numpy.ndarray
        rescaled image
    """
    if rescale_mode == "percentiles":
        in_range = np.percentile(image, rescale_range, axis=(1, 2)).T
    elif rescale_mode == "values":
        in_range = np.array(rescale_range).reshape(-1, 2)
        if in_range.shape[0] == 1:
            in_range = [tuple(in_range[0]) for _ in range(image.shape[0])]
    else:
        raise RuntimeError(f"unknown rescale_mode {rescale_mode}")

    return np.array([
            exposure.rescale_intensity(
                image[i, :, :], in_range=tuple(in_range[i]), out_range=(1, 255)
            ).astype(np.uint8)
            for i in range(image.shape[0])
        ])


def calculate_raster_percentiles(raster, lower_cut=2, upper_cut=98, sample_size=128, size=2048):
    size = (size, size)

    with rasterio.open(raster) as ds:
        windows = list(sliding_windows(size, size, ds.width, ds.height))
        _logger.info("Windows: %d, sample size: %d", len(windows), sample_size)
        totals_per_bands = [[] for _ in range(ds.count)]
        for window, _ in tqdm(windows):
            img = ds.read(window=window).astype(np.float)
            img[img == ds.nodata] = np.nan
            if np.isnan(img).all():
                continue
            window_sample = []
            for i in range(img.shape[0]):
                values = img[i].flatten()
                window_sample.append(
                    np.random.choice(values, size=sample_size, replace=False)
                )
            for i, win in enumerate(window_sample):
                totals_per_bands[i].append(win)

        for i, totals in enumerate(totals_per_bands):
            totals_per_bands[i] = np.array(totals).flatten()

        totals = np.array(totals_per_bands)
        _logger.info("Total shape: %s", totals.shape)

        res = tuple(
            tuple(p) for p in np.nanpercentile(totals, (lower_cut, upper_cut), axis=1).T
        )
        _logger.info("Percentiles: %s", res)

        return res


def write_chips_geojson(output_path, chip_pairs, *, type, crs, basename):
    if not chip_pairs:
        _logger.warn("No chips to save")
        return

    _logger.info("Write chips geojson")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        d = {"type": "FeatureCollection", "features": []}
        for i, (chip, (_fi, xi, yi)) in enumerate(chip_pairs):
            # Shapes will be stored in EPSG:4326 projection
            if crs != "epsg:4326":
                chip_wgs = reproject_shape(chip, crs, "epsg:4326")
            else:
                chip_wgs = chip
            filename = f"{basename}_{xi}_{yi}.{type}"
            feature = {
                "type": "Feature",
                "geometry": mapping(chip_wgs),
                "properties": {"id": i, "x": xi, "y": yi, "filename": filename},
            }
            d["features"].append(feature)
        f.write(json.dumps(d))


def get_raster_band_count(path):
    with rasterio.open(path) as src:
        return src.count
