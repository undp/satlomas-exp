#!/usr/bin/env python3
import csv
import os
import subprocess
import sys
from glob import glob
from datetime import datetime


def run_command(cmd):
    print(cmd)
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)


def list_files(prefix):
    bucket = 'sentinel-s1-l1c'
    cmd = run_command(f'aws s3 ls s3://{bucket}/{prefix} --request-payer')
    out = cmd.stdout.decode("utf-8")
    lines = [line.strip().split() for line in out.split("\n")]
    lines = [line for line in lines if line]
    files = [line[1] for line in lines]
    return [f'{prefix}{file}' for file in files]


def download_product(product_id, outdir):
    bucket = 'sentinel-s1-l1c'
    p_outdir = os.path.join(outdir, product_id)

    if os.path.exists(p_outdir) and glob(os.path.join(p_outdir, '*')):
        print(p_outdir, "already downloaded")
        return

    os.makedirs(p_outdir, exist_ok=True)

    date = product_id.split('_')[4]
    prefix = datetime.strptime(date, '%Y%m%dT%H%M%S').strftime('%Y/%-m/%-d')
    path = f'GRD/{prefix}/IW/'

    for dirname in list_files(path):
        src = f'{dirname}{product_id}/'
        run_command(f'aws s3 cp s3://{bucket}/{src} {p_outdir} --recursive --request-payer')


s1_list = sys.argv[1]
outdir = sys.argv[2]

with open(s1_list) as f:
    csv_reader = csv.reader(f)
    for row in csv_reader:
        download_product(row[0], outdir)
