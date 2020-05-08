#!/bin/bash
set -xeu -o pipefail

# TODO
# * Validar with test datasets

dataset_dir=data/datasets/sen
results_dir=data/results/sen

function polygon_stats {
  dataset=$1
  date_range=$2
  feats_image=$results_dir/features_${dataset}_${date_range}.tif

  otbcli_PolygonClassStatistics  \
    -vec $dataset_dir/$dataset/$date_range/poly.shp  \
    -in $feats_image  \
    -field "class"  \
    -out $results_dir/stats_${dataset}_${date_range}.xml
}

function sample_selection {
  dataset=$1
  date_range=$2
  feats_image=$results_dir/features_${dataset}_${date_range}.tif

  otbcli_SampleSelection  \
    -in $feats_image  \
    -vec $dataset_dir/$dataset/$date_range/poly.shp  \
    -field "class"  \
    -instats $results_dir/stats_${dataset}_${date_range}.xml  \
    -out $results_dir/pos_${dataset}_${date_range}.shp
}

function sample_extraction {
  # Extract the pixels values at samples locations (Learning data)
  dataset=$1
  date_range=$2
  feats_image=$results_dir/features_${dataset}_${date_range}.tif

  otbcli_SampleExtraction  \
    -in $feats_image  \
    -vec $results_dir/pos_${dataset}_${date_range}.shp  \
    -field "class"  \
    -out $results_dir/samples_${dataset}_${date_range}.shp
}

function merge_samples {
  dataset=$1

  name=merged_samples_${dataset}
  out=$results_dir/${name}.shp

  for i in $results_dir/samples_${dataset}_*.shp; do
    if [ -f "$out" ]; then
      echo "creating $out"
      ogr2ogr -f "ESRI Shapefile" -update -append $out $i -nln $name
    else
      echo "merging..."
      ogr2ogr -f "ESRI Shapefile" $out $i
    fi
  done
}

function train_classifier {
  # Train a Random Forest classifier with validation
  vd_path=$1
  features=$(printf "value_%d " {0..233})

  otbcli_TrainVectorClassifier  \
    -io.vd $vd_path  \
    -cfield "class"  \
    -feat $features  \
    -classifier "rf"  \
    -classifier.rf.max 9 \
    -classifier.rf.nbtrees 175 \
    -io.out data/results/rf_model.yaml

  #-valid.vd "data/results/rf_test_samples.shp" \
}

function classify_image {
  out=$1

  otbcli_ImageClassifier  \
    -in     $results_dir/feature_image.tif  \
    -model  data/results/rf_model.yaml  \
    -out    $out
}

dataset=train
for date_range in $(ls $dataset_dir/train/); do
  polygon_stats     $dataset $date_range
  sample_selection  $dataset $date_range
  sample_extraction $dataset $date_range
  merge_samples     $dataset
done
train_classifier $results_dir/merged_samples_train.shp
