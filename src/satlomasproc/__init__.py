# -*- coding: utf-8 -*-
import logging

from pkg_resources import DistributionNotFound, get_distribution

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = "unknown"
finally:
    del get_distribution, DistributionNotFound

# Set null handler to avoid printing to sys.error by default, if package user
# does not configure any handler.
logging.getLogger("satlomasproc").addHandler(logging.NullHandler())
