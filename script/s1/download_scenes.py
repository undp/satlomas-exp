#!/usr/bin/env python3
from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date
import os

from_date = date(2018, 11, 1)
to_date   = date(2019,  1, 1)

root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
aoi_path = os.path.join(root_path, 'data', 'aoi_4326.geojson')
download_path = os.path.join(root_path, 'data', 'images', 's1', '_real')

api = SentinelAPI(os.getenv("SCIHUB_USER"), os.getenv("SCIHUB_PASS"), 'https://scihub.copernicus.eu/dhus')

footprint = geojson_to_wkt(read_geojson(aoi_path))
products = api.query(footprint,
                     date=(from_date, to_date),
                     platformname='Sentinel-1',
                     producttype='GRD',
                     polarisationmode='VV VH',
                     orbitdirection='ASCENDING')

for k, p in products.items():
    print((k, p['summary']))

os.makedirs(download_path, exist_ok=True)

results = api.download_all(products, directory_path=download_path)
print(results)
