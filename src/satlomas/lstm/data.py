# -*- coding: utf-8 -*-
"""Util functions to read data from different sources"""

import logging
import pandas as pd
import sys


from satlomas import __version__

__author__ = "Leandro Abraham"
__copyright__ = "Dymaxion Labs"
__license__ = "apache-2.0"

# _logger = logging.getLogger(__name__)
# logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
# loglevel = logging.DEBUG
# logging.basicConfig(level=loglevel, stream=sys.stdout,format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def read_time_series_from_csv(
    dataset_filename="../data/meteorologico/sudeste.csv",
    date_col="date",
    hr_col="hr",
    numeric_var="temp",
    sensor_var="inme",
):
    """Reads a time series from csv"""
    cols_to_read = [date_col] + [hr_col] + [numeric_var] + [sensor_var]

    dataset = pd.read_csv(
        dataset_filename, header=0, index_col=0, nrows=None, usecols=cols_to_read
    )
    # TO DO : esto tiene que logearse por el logger general, NO imprimirse
    print("read dataset of shape {}".format(dataset.shape))

    # agregar hora y demás a datetime lo hace muy costoso ?
    # dataset['timestamp']=pd.to_datetime(dataset[date_col]+ ' ' + dataset[hr_col].to_string()+':00:00')
    # dataset[date_col]=pd.to_datetime(dataset[date_col])
    dataset.sort_values([date_col, hr_col], inplace=True, ascending=True)
    dataset.reset_index(inplace=True)

    return dataset


def read_time_series_from_db(
    sensor="A601",
    date_col="date",
    hr_col="hr",
    min_col="minute",
    numeric_var="temperature",
    sensor_var="inme",  # TODO : change this for station_code in all the script
    date_since=None,
    which_minutes=[0, 15, 30, 45],
):
    # get the station (sensor)
    # station = Station.objects.get(code=sensor)
    # get all the measurements from this station
    measurements = Measurement.objects.filter(
        station=Station.objects.get(code=sensor).id
    )
    if date_since is not None:
        measurements = measurements.filter(datetime__gte=date_since)

    self.log_success(
        "Measurements to read from database for sensor {} with query \n{}".format(
            sensor, measurements.query
        )
    )
    # get a dataframe from the measurements
    dataset = pd.DataFrame(list(measurements.values("datetime", "attributes")))
    self.log_success("Dataset from database of shape {}".format(dataset.shape))
    # parse datetime column to get sepearae date, hr and minute columns
    dataset[date_col] = dataset.datetime.dt.date
    dataset[hr_col] = dataset.datetime.dt.hour
    dataset[min_col] = dataset.datetime.dt.minute
    # get the numeric var column parsing the json
    dataset[numeric_var] = dataset.attributes.apply(lambda x: x[numeric_var])
    dataset[sensor_var] = sensor

    # sort and re-index before returning
    dataset.sort_values([date_col, hr_col], inplace=True, ascending=True)
    dataset.reset_index(inplace=True)

    return dataset.loc[dataset.minute.isin(which_minutes)]
