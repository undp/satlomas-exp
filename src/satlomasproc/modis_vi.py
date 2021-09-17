import logging
import os
import datetime
import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from satlomasproc.utils import run_command

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)


HEADERS = {"User-Agent": "get_modis Python 3"}
CHUNKS = 65536

MODIS_PLATFORM = "MOLA"
MODIS_PRODUCT = "MYD13Q1.006"
H_PERU = "10"
V_PERU = "10"


def as_date(datetime_or_date):
    if isinstance(datetime_or_date, datetime.date):
        return datetime_or_date
    elif isinstance(datetime_or_date, datetime.datetime):
        return datetime_or_date.date()
    else:
        raise ValueError(f"invalid date or datetime: {datetime_or_date}")


def split_date_interval(date_from, date_to):
    """Split date interval into yearly sub-intervals"""
    date_from = as_date(date_from)
    date_to = as_date(date_to)
    years = range(date_from.year, date_to.year + 1)
    if len(years) == 1:
        return [(date_from, date_to)]
    dates = []
    for i, year in enumerate(years):
        if i == 0:
            dt_to = datetime.date(year, 12, 31)
            if dt_to != date_from:
                dates.append((date_from, dt_to))
        elif i == len(years) - 1:
            dt_from = datetime.date(year, 1, 1)
            if dt_from != date_to:
                dates.append((dt_from, date_to))
        else:
            dates.append((datetime.date(year, 1, 1), datetime.date(year, 12, 31)))
    return dates


def download_modis_vi_images(output_dir=".", *, date_from, date_to, username, password):
    date_intervals = split_date_interval(date_from, date_to)
    all_files = []
    for dt_from, dt_to in date_intervals:
        year = dt_to.year
        doy_begin = dt_from.timetuple().tm_yday
        doy_end = dt_to.timetuple().tm_yday

        logger.info("Download MODIS hdf files")
        tile = "h{}v{}".format(H_PERU, V_PERU)

        files = get_modisfiles(
            username,
            password,
            MODIS_PLATFORM,
            MODIS_PRODUCT,
            year,
            tile,
            proxy=None,
            doy_start=doy_begin,
            doy_end=doy_end,
            out_dir=output_dir,
            verbose=True,
            ruff=False,
            get_xml=False,
        )
        all_files.extend(files)

    return sorted(all_files)


def get_modisfiles(
    username,
    password,
    platform,
    product,
    year,
    tile,
    proxy,
    doy_start=1,
    doy_end=-1,
    base_url="https://e4ftl01.cr.usgs.gov",
    out_dir=".",
    ruff=False,
    get_xml=False,
    verbose=False,
):
    """Download MODIS products for a given tile, year & period of interest

    This function uses the `urllib2` module to download MODIS "granules" from
    the USGS website. The approach is based on downloading the index files for
    any date of interest, and parsing the HTML (rudimentary parsing!) to search
    for the relevant filename for the tile the user is interested in. This file
    is then downloaded in the directory specified by `out_dir`.

    The function also checks to see if the selected remote file exists locally.
    If it does, it checks that the remote and local file sizes are identical.
    If they are, file isn't downloaded, but if they are different, the remote
    file is downloaded.

    Parameters
    ----------
    username: str
        The EarthData username string
    password: str
        The EarthData username string
    platform: str
        One of three: MOLA, MOLT MOTA
    product: str
        The product name, such as MOD09GA.005 or MYD15A2.005. Note that you
        need to specify the collection number (005 in the examples)
    year: int
        The year of interest
    tile: str
        The tile (e.g., "h17v04")
    proxy: dict
        A proxy definition, such as {'http': 'http://127.0.0.1:8080', \
        'ftp': ''}, etc.
    doy_start: int
        The starting day of the year.
    doy_end: int
        The ending day of the year.
    base_url: str, url
        The URL to use. Shouldn't be changed, unless USGS change the server.
    out_dir: str
        The output directory. Will be create if it doesn't exist
    ruff: Boolean
        Check to see what files are already available and download them without
        testing for file size etc.
    verbose: Boolean
        Whether to sprout lots of text out or not.
    get_xml: Boolean
        Whether to get the XML metadata files or not. Someone uses them,
        apparently ;-)
    Returns
    -------
    Nothing
    """

    if proxy is not None:
        proxy = urllib2.ProxyHandler(proxy)
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)

    if not os.path.exists(out_dir):
        if verbose:
            logger.info("Creating output dir %s" % out_dir)
        os.makedirs(out_dir)
    if doy_end == -1:
        if calendar.isleap(year):
            doy_end = 367
        else:
            doy_end = 366

    dates = [
        time.strftime("%Y.%m.%d", time.strptime("%d/%d" % (i, year), "%j/%Y"))
        for i in range(doy_start, doy_end)
    ]
    url = "%s/%s/%s/" % (base_url, platform, product)
    dates = parse_modis_dates(url, dates, product, out_dir, ruff=ruff)

    # Only use the latests date from range
    if len(dates) > 1:
        dates = [dates[-1]]

    them_urls = []
    res = []
    for date in dates:
        r = requests.get("%s%s" % (url, date), verify=False)
        for line in r.text.split("\n"):
            if line.find(tile) >= 0:
                if line.find(".hdf") >= 0:
                    fname = line.split("href=")[1].split(">")[0].strip('"')
                    if fname.endswith(".hdf.xml") and not get_xml:
                        pass
                    else:
                        fpath = os.path.join(out_dir, fname)
                        res.append(fpath)
                        if not os.path.exists(fpath):
                            them_urls.append("%s/%s/%s" % (url, date, fname))
                        else:
                            if verbose:
                                logger.info("File %s already present. Skipping" % fname)

    with requests.Session() as s:
        s.auth = (username, password)
        for the_url in them_urls:
            r1 = s.request("get", the_url)
            r = s.get(r1.url, stream=True)

            if not r.ok:
                raise IOError("Can't start download... [%s]" % the_url)
            file_size = int(r.headers["content-length"])
            fname = the_url.split("/")[-1]
            fpath = os.path.join(out_dir, fname)
            logger.info("Starting download on %s(%d bytes) ..." % (fpath, file_size))
            with open(fpath, "wb") as fp:
                for chunk in r.iter_content(chunk_size=CHUNKS):
                    if chunk:
                        fp.write(chunk)
                fp.flush()
                os.fsync(fp)
                if verbose:
                    logger.info("\tDone!")

    if verbose:
        logger.info("Completely finished downlading all there was")

    return res


def parse_modis_dates(url, dates, product, out_dir, ruff=False):
    """Parse returned MODIS dates.

    This function gets the dates listing for a given MODIS products, and
    extracts the dates for when data is available. Further, it crosses these
    dates with the required dates that the user has selected and returns the
    intersection. Additionally, if the `ruff` flag is set, we'll check for
    files that might already be present in the system and skip them. Note
    that if a file failed in downloading, it might still be around
    incomplete.

    Parameters
    ----------
    url: str
        A URL such as "http://e4ftl01.cr.usgs.gov/MOTA/MCD45A1.005/"
    dates: list
        A list of dates in the required format "YYYY.MM.DD"
    product: str
        The product name, MOD09GA.005
    out_dir: str
        The output dir
    ruff: bool
        Whether to check for present files
    Returns
    -------
    A (sorted) list with the dates that will be downloaded.
    """
    already_here_dates = []
    if ruff:
        product = product.split(".")[0]
        already_here = fnmatch.filter(os.listdir(out_dir), "%s*hdf" % product)
        already_here_dates = [x.split(".")[-5][1:] for x in already_here]

    html = return_url(url)

    available_dates = []
    for line in html:

        if line.decode().find("href") >= 0 and line.decode().find("[DIR]") >= 0:
            # Points to a directory
            the_date = line.decode().split('href="')[1].split('"')[0].strip("/")
            if ruff:
                try:
                    modis_date = time.strftime(
                        "%Y%j", time.strptime(the_date, "%Y.%m.%d")
                    )
                except ValueError:
                    continue
                if modis_date in already_here_dates:
                    continue
                else:
                    available_dates.append(the_date)
            else:
                available_dates.append(the_date)

    dates = set(dates)
    available_dates = set(available_dates)
    suitable_dates = list(dates.intersection(available_dates))
    suitable_dates.sort()
    return suitable_dates


def return_url(url):
    the_day_today = time.asctime().split()[0]
    the_hour_now = int(time.asctime().split()[3].split(":")[0])
    if the_day_today == "Wed" and 14 <= the_hour_now <= 17:
        logger.info("Sleeping for %d hours... Yawn!" % (18 - the_hour_now))
        time.sleep(60 * 60 * (18 - the_hour_now))

    req = urllib2.Request("%s" % (url), None, HEADERS)
    html = urllib2.urlopen(req).readlines()
    return html


def extract_subdatasets_as_gtiffs(files, tif_dir):
    logger.info("Extract subdatasets as GeoTIFFs")
    for src in files:
        name, _ = os.path.splitext(os.path.basename(src))
        dst = os.path.join(tif_dir, name)
        if not os.path.exists(f"{dst}_ndvi.tif"):
            run_command(
                f"gdal_translate "
                f'HDF4_EOS:EOS_GRID:{src}:MODIS_Grid_16DAY_250m_500m_VI:"250m 16 days NDVI" '
                f"{dst}_ndvi.tif"
            )
        if not os.path.exists(f"{dst}_pixelrel.tif"):
            run_command(
                f"gdal_translate "
                f'HDF4_EOS:EOS_GRID:{src}:MODIS_Grid_16DAY_250m_500m_VI:"250m 16 days pixel reliability" '
                f"{dst}_pixelrel.tif"
            )


def extract_date_from_modis_filename(filename):
    """Extract date from MODIS filename, which contains year and doy encoded in it"""
    name, _ = os.path.splitext(os.path.basename(filename))
    date_part = name.split(".")[1]
    year = int(date_part[1:5])
    doy = int(date_part[5:])
    return datetime.date(year, 1, 1) + datetime.timedelta(doy - 1)
