#!/usr/bin/env python3
import subprocess
import argparse
import os
from pathlib import Path


def run_command(cmd):
    print(cmd)
    subprocess.run(cmd, shell=True, check=True)


def concatenate_images(*, src, dst):
    src = " ".join(str(s) for s in src)
    run_command(f'otbcli_ConcatenateImages -il {src} -out {dst}')


def band_math(*, src, dst, exp):
    src = " ".join(str(s) for s in src)
    run_command(f'otbcli_BandMath -il {src} -out {dst} -exp "{exp}"')


def clip_raster(*, src, dst, aoi):
    run_command(f'gdalwarp -of GTiff -cutline {aoi} -crop_to_cutline {src} {dst}')


def main(args):
    # Get image .SAFE directory
    input_dir = Path(args.input)
    output_dir = Path(args.output)

    for scene_dir in input_dir.glob("*.SAFE"):
        scene_output_dir = output_dir / scene_dir.stem
        os.makedirs(scene_output_dir, exist_ok=True)

        # Gather images per resolution
        r10m_dir = next(scene_dir.glob("GRANULE/*/IMG_DATA/R10m/"))
        r10m_b04 = next(r10m_dir.glob('*_B04_*.jp2'))
        r10m_b03 = next(r10m_dir.glob('*_B03_*.jp2'))
        r10m_b02 = next(r10m_dir.glob('*_B02_*.jp2'))
        r10m_b08 = next(r10m_dir.glob('*_B08_*.jp2'))

        r20m_dir = next(scene_dir.glob("GRANULE/*/IMG_DATA/R20m/"))
        r20m_b05 = next(r20m_dir.glob('*_B05_*.jp2'))
        r20m_b06 = next(r20m_dir.glob('*_B06_*.jp2'))
        r20m_b07 = next(r20m_dir.glob('*_B07_*.jp2'))
        r20m_b8a = next(r20m_dir.glob('*_B8A_*.jp2'))
        r20m_b11 = next(r20m_dir.glob('*_B11_*.jp2'))
        r20m_b12 = next(r20m_dir.glob('*_B12_*.jp2'))

        # Generate VI images
        # NDVI
        r10m_ndvi = scene_output_dir / 's2_10m_nvdi.tif'
        if not r10m_ndvi.exists():
            band_math(src=[r10m_b08, r10m_b04],
                      dst=r10m_ndvi,
                      exp='(im1b1 - im2b1) / (im1b1 + im2b1)')
        # NDWI - Gao 1996
        #r20m_ndwi = scene_output_dir / 's2_20m_ndwi.tif'
        #band_math(src=[r20m_b08, r20m_b12],
        #          dst=r20m_ndwi,
        #          exp='(im1b1 - im2b1) / (im1b1 + im2b1)')
        # EVI
        r10m_evi = scene_output_dir / 's2_10m_evi.tif'
        if not r10m_evi.exists():
            band_math(src=[r10m_b08, r10m_b04],
                      dst=r10m_evi,
                      exp='(2.4 * (im1b1 - im2b1) / (im1b1 + im2b1 + 1.0))')
        # SAVI
        #r10m_savi = scene_output_dir / 's2_10m_savi.tif'
        #band_math(src=[r10m_b08, r10m_b04],
        #          dst=r10m_savi,
        #          exp='(im1b1 - im2b1) / (im1b1 + im2b1 + 0.428) * (1.0 + 0.428)')

        # Concatenate 20mb multiband image
        src = [r20m_b05, r20m_b06, r20m_b07, r20m_b8a, r20m_b11, r20m_b12]
        dst = scene_output_dir / 's2_20m.tif'
        if not dst.exists():
            concatenate_images(src=src, dst=dst)

        # Concatenate 10m multiband image
        src = [r10m_b04, r10m_b03, r10m_b02, r10m_b08, r10m_ndvi, r10m_evi]
        dst = scene_output_dir / 's2_10m.tif'
        if not dst.exists():
            concatenate_images(src=src, dst=dst)

    # Merge results into a single .vrt file and clip to AOI
    for p in ['s2_20m.tif', 's2_10m.tif']:
        src = ' '.join(str(s) for s in output_dir.glob(f'*/{p}'))
        dst = output_dir / f'{Path(p).stem}.vrt'
        if not dst.exists():
            run_command(f'gdalbuildvrt {dst} {src}')

        clip_dst = output_dir / p
        if not clip_dst.exists():
            clip_raster(src=dst, dst=clip_dst, aoi=args.aoi)

    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preprocess Sentinel-2 images into dataset for training or prediction.')
    parser.add_argument('input', help='input directory with .SAFE dirs')
    parser.add_argument('output', help='output directory')
    parser.add_argument('--aoi', '-a', help='AOI vector file')

    args = parser.parse_args()
    main(args)
