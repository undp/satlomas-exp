#!/bin/bash
set -xeu -o pipefail

dataset_dir=~/geolomas-exp/data/datasets/sen
results_dir=~/geolomas-exp/data/results/sen

function superimpose {
  input_dir=$1
  output_dir=$2

  out=$output_dir/$3.tif
  if [ ! -f "$out" ]; then
    otbcli_Superimpose  \
      -inm  $input_dir/$3.tif  \
      -inr  $input_dir/$4.tif  \
      -out  $out
  fi
}

function extract_all_features {
  feat_dir=$1

  for band in $(seq 1 8); do
    extract_local_stats   s2_10m $band $feat_dir
    extract_haralick      s2_10m $band $feat_dir
  done

  for band in $(seq 1 6); do
    extract_local_stats   s2_20m $band $feat_dir
    extract_haralick      s2_20m $band $feat_dir
  done

  for band in $(seq 1 3); do
    extract_local_stats   s1 $band $feat_dir
    extract_haralick      s1 $band $feat_dir
  done

  extract_local_stats   srtm 1 $feat_dir
  extract_haralick      srtm 1 $feat_dir
}

function extract_local_stats {
  image=$1
  band=$2
  feat_dir=$3

  out=$feat_dir/local_stats_$1_$2.tif
  if [ ! -f "$out" ]; then
    otbcli_LocalStatisticExtraction  \
      -in        $feat_dir/$image.tif  \
      -channel   $band  \
      -radius    3  \
      -out       $out
  fi
}

function extract_haralick {
  feat_dir=$3

  out=$feat_dir/haralick_$1_$2.tif
  if [ ! -f "$out" ]; then
    otbcli_HaralickTextureExtraction  \
      -in             $feat_dir/$1.tif  \
      -channel        $2  \
      -texture        simple  \
      -parameters.min 0  \
      -parameters.max 0.3  \
      -out            $out
  fi
}

function concatenate_images {
  input_dir=$1
  output_path=$2

  current_dir=$(pwd)

  cd $input_dir
  if [ ! -f "$output_path" ]; then
    otbcli_ConcatenateImages  \
      -il   $(ls)  \
      -out  $output_path
  fi
  cd $current_dir
}


for set in train test; do
  for date_range in $(cd $dataset_dir/$set && ls); do
    feat_dir=$results_dir/feats/${set}_${date_range}
    mkdir -p $feat_dir

    # Copy S2 10m image to feats/
    cp $dataset_dir/$set/$date_range/s2_10m.tif $feat_dir/s2_10m.tif

    # Superimpose the other images in reference to S2 10m image
    superimpose $dataset_dir/$set/$date_range $feat_dir s2_20m s2_10m
    superimpose $dataset_dir/$set/$date_range $feat_dir s1     s2_10m
    superimpose $dataset_dir/$set/$date_range $feat_dir srtm   s2_10m

    extract_all_features $feat_dir

    concatenate_images $feat_dir $results_dir/features_${set}_${date_range}.tif
  done
done
