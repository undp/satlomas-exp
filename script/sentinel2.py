#!/usr/bin/env python3
from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date
import os

fecha_desde = date(2018, 11, 1)
fecha_hasta = date(2019, 1, 1)

root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
aoi_path = os.path.join(root_path, 'data', 'aoi_4326.geojson')

fechas = (fecha_desde, fecha_hasta)

# connect to the API
api = SentinelAPI(os.getenv("USUARIO"), os.getenv("PASSWORD"), 'https://scihub.copernicus.eu/dhus')

# download single scene by known product id
#api.download(<product_id>)

# search by polygon, time, and Hub query keywords
footprint = geojson_to_wkt(read_geojson(aoi_path))

products = api.query(footprint,
        date=fechas,
        platformname='Sentinel-2',
        cloudcoverpercentage=(0, 100))
print(products)

# download all results from the search
result = api.download_all(products)
print(result)

# GeoJSON FeatureCollection containing footprints and metadata of the scenes
#api.to_geojson(products)

# GeoPandas GeoDataFrame with the metadata of the scenes and the footprints as geometries
#api.to_geodataframe(products)

# Get basic information about the product: its title, file size, MD5 sum, date, footprint and
# its download url
#api.get_product_odata(<product_id>)

# Get the product's full metadata available on the server
#api.get_product_odata(<product_id>, full=True)
