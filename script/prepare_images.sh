#!/bin/bash
set -xeu -o pipefail

root_dir=~/geolomas-exp
images_dir=$root_dir/data/images
full_dir=$images_dir/full

for set in train test; do
  date_ranges=$(cd $root_dir/data/datasets/sen/$set && ls)
  s2_img_dir=$images_dir/s2/$set
  s1_img_dir=$images_dir/s1/$set

  for date_range in $date_ranges; do
    mkdir -p $full_dir/$date_range

    # S2
    ln -fs $s2_img_dir/s2_${set}_${date_range}_10m.tif $full_dir/$date_range/s2_10m.tif
    ln -fs $s2_img_dir/s2_${set}_${date_range}_20m.tif $full_dir/$date_range/s2_20m.tif

    # S1
    ln -fs $s1_img_dir/s1_${set}_${date_range}.tif $full_dir/$date_range/s1.tif

    # SRTM
    ln -fs $images_dir/srtm/1arc_v3_unificado_2.tif $full_dir/$date_range/srtm.tif
  done
done
