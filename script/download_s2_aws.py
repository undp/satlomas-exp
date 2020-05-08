#!/usr/bin/env python3
import csv
import subprocess
import sys


def run_command(cmd):
    print(cmd)
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)


s2_list = sys.argv[1]
outdir = sys.argv[2]

with open(s2_list) as f:
    csv_reader = csv.reader(f)
    for row in csv_reader:
        product_id = row[0]
        run_command(f'sentinelhub.aws --product {product_id} -f {outdir}')
