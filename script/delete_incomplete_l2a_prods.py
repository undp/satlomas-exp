#!/usr/bin/env python3
import os
import sys
import shutil
from glob import glob

# Check if R10m, R20m and R60m are created
# Check if R10m has 7 .jp2 files
# Check if R20m has 13 .jp2 files
# Chec kif R60m has 15 .jp2 files

def is_complete(product_path):
    img_data_p = os.path.join(product_path, 'GRANULE/*/IMG_DATA')
    files = [glob(os.path.join(img_data_p, t, '*.jp2')) for t in ['R10m', 'R20m', 'R60m']]
    counts = [len(fs) for fs in files]
    expected_counts = [7, 13, 15]
    return all(c == e for c, e in zip(counts, expected_counts))


def main():
    base_dir = sys.argv[1]
    for p_path in glob(os.path.join(base_dir, '*.SAFE')):
        if not is_complete(p_path):
            print(p_path, "deleted")
            shutil.rmtree(p_path)


if __name__ == "__main__": main()
