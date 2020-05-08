#!/bin/bash
set -xeu -o pipefail

# Postprocess
#
# 1. Extract mask of "land movement" (class 2) from cover.tif
# 2. Polygonize mask
# 3. Clip mask to inclusion AOI shapefile
#

inclusion_vector=~/dym/geolomas-exp/data/lomas.geojson

function extract_land_movement_mask {
  otbcli_BandMath -il $1 -out $2 -exp "im1b1 == 2"
}

function clip_raster {
  rm -f $2
  gdalwarp -of GTiff -cutline $inclusion_vector -crop_to_cutline $1 $2
}

function polygonize_mask {
  gdal_polygonize.py $1 $2
}

#function clip_mask {
#  ogr2ogr -f GeoJSON -clipsrc $inclusion_vector $2 $1
#}

extract_land_movement_mask $1 /tmp/land_mov_mask.tif
clip_raster /tmp/land_mov_mask.tif /tmp/clipped_land_mov_mask.tif
polygonize_mask /tmp/clipped_land_mov_mask.tif /tmp/land_mov_mask.shp
