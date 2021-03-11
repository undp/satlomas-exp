#!/bin/bash
set -xeu -o pipefail

function superimpose {
  otbcli_Superimpose  \
    -inr  $dataset_dir/$2.tif  \
    -inm  $dataset_dir/$1.tif  \
    -out  $results_dir/feats/$1.tif
}

function extract_all_features {
  for band in $(seq 1 8); do
    extract_local_stats   s2_10m $band
    extract_haralick      s2_10m $band
  done

  for band in $(seq 1 6); do
    extract_local_stats   s2_20m $band
    extract_haralick      s2_20m $band
  done

  for band in $(seq 1 3); do
    extract_local_stats   s1 $band
    extract_haralick      s1 $band
  done

  extract_local_stats   srtm 1
  extract_haralick      srtm 1
}

function extract_local_stats {
  otbcli_LocalStatisticExtraction  \
    -in        $results_dir/feats/$1.tif  \
    -channel   $2  \
    -radius    3  \
    -out       $results_dir/feats/local_stats_$1_$2.tif
}

function extract_haralick {
  otbcli_HaralickTextureExtraction  \
    -in             $results_dir/feats/$1.tif  \
    -channel        $2  \
    -texture        simple  \
    -parameters.min 0  \
    -parameters.max 0.3  \
    -out            $results_dir/feats/haralick_$1_$2.tif
}

function concatenate_images {
  current_dir=$(pwd)
  cd $results_dir/feats
  otbcli_ConcatenateImages  \
    -il   $(ls)  \
    -out  $results_dir/features.tif
  cd $current_dir
}

function classify_image {
  otbcli_ImageClassifier  \
    -in     $results_dir/features.tif  \
    -model  data/results/rf_model.yaml  \
    -out    $results_dir/cover.tif
}

function post_process_result {
  script/post_process_sen.sh $results_dir/cover.tif $results_dir/cover.geojson
}

function predict_set {
  date_ranges=$1
  for date_range in $date_ranges; do
    dataset_dir=~/satlomas-exp/data/images/full/$date_range
    results_dir=~/satlomas-exp/data/results/full/$date_range

    if [ ! -f "$results_dir/cover.tif" ]; then
      mkdir -p $results_dir/feats

      # Copy S2 10m image to feats/
      cp $dataset_dir/s2_10m.tif $results_dir/feats/s2_10m.tif
      # Superimpose the other images in reference to S2 10m image
      superimpose s2_20m s2_10m
      superimpose s1     s2_10m
      superimpose srtm   s2_10m

      extract_all_features
      concatenate_images
      classify_image
    fi

    if [ ! -f "$results_dir/cover.geojson" ]; then
      post_process_result
    fi
  done
}

predict_set "201811_201812 201901_201902 201903_201904 201905_201906 201907_201908 201909_201910"
