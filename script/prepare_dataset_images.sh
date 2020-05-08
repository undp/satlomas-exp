#!/bin/bash
set -xeu -o pipefail

dataset_dir=data/datasets/sen
images_dir=data/images
area_cutline=$dataset_dir/areas.geojson
area_layer_name=areas

function clip_raster {
  rm -f $2
  gdalwarp \
    -of GTiff \
    -cutline $area_cutline \
    -cl $area_layer_name \
    -crop_to_cutline \
    -co COMPRESS=DEFLATE \
    -co PREDICTOR=2 \
    -co ZLEVEL=9 \
    $1 $2
}

for set in train test; do
  clip_raster \
    $images_dir/srtm/1arc_v3_unificado_2.tif \
    $dataset_dir/srtm.tif

  for date_range in $(cd $dataset_dir/$set && ls); do
    mkdir -p $dataset_dir/$set/$date_range

    # S2 10m
    clip_raster \
      $images_dir/s2/$set/s2_${date_range}_10m.tif \
      $dataset_dir/$set/$date_range/s2_10m.tif

    # S2 20m
    clip_raster \
      $images_dir/s2/$set/s2_${date_range}_20m.tif \
      $dataset_dir/$set/$date_range/s2_20m.tif

    # S1
    clip_raster \
      $images_dir/s1/$set/s1_${date_range}.tif \
      $dataset_dir/$set/$date_range/s1.tif

    # Copy SRTM (static image)
    cp $dataset_dir/srtm.tif $dataset_dir/$set/$date_range/
  done
done
