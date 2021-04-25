import subprocess

import logging


def run_command(cmd):
    logging.info(cmd)
    subprocess.run(cmd, shell=True, check=True)
