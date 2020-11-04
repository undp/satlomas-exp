#!/bin/bash

# Merge predict result chips into a single geotiff
gdal_merge.py -co TILED=YES -co COMPRESS=DEFLATE -o $f/results_v8.tif $f/results_v8/*.tif

# Clip result geotiff to AOI
gdalwarp -of GTiff -cutline /home/ro/data/lomas/unet-sen2/train/20200420/aoi.geojson -cl aoi -crop_to_cutline -dstalpha -co TILED=YES /home/ro/data/lomas/unet-sen2/train/160_160_20190411/results_v8.tif /home/ro/data/lomas/unet-sen2/train/160_160_20190411/results_v8_clip.tif
