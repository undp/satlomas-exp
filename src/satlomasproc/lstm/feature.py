# -*- coding: utf-8 -*-
"""Util functions to make data processing and feature engineering"""

import pandas as pd
import pickle
import sys


from satlomasproc import __version__
from sklearn.preprocessing import MinMaxScaler

__author__ = "Leandro Abraham"
__copyright__ = "Dymaxion Labs"
__license__ = "apache-2.0"


def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
    """
    Convert series of data to supervised squence learning

    """
    n_vars = 1 if type(data) is list else data.shape[1]
    df = data
    cols, names = list(), list()
    # input sequence (t-n, ... t-1)
    for i in range(n_in, 0, -1):
        cols.append(df.shift(i))
        names += ["{}_t-{}".format(var_name, i) for var_name in df.columns]

    # forecast sequence (t, t+1, ... t+n)
    for i in range(0, n_out):
        cols.append(df.shift(-i))
        if i == 0:
            names += ["{}_t".format(var_name) for var_name in df.columns]
        else:
            names += ["{}_t+{}".format(var_name, i) for var_name in df.columns]
    # put it all together
    agg = pd.concat(cols, axis=1)
    agg.columns = names
    # drop rows with NaN values
    if dropnan:
        agg.dropna(inplace=True)
    return agg


def get_interest_variable(
    in_dataset, sensor_var, date_col, hr_col, numeric_var, target_sensor="A620"
):
    """
    Extract var to predict on from dataset

    """
    dataset_pproc = in_dataset.loc[
        in_dataset[sensor_var] == target_sensor, [date_col, hr_col] + [numeric_var]
    ]
    hrs_str = dataset_pproc[hr_col].to_string()
    dates_str = dataset_pproc[date_col]

    dataset_pproc[date_col] = pd.to_datetime(dataset_pproc[date_col])
    dataset_pproc.set_index([date_col, hr_col], inplace=True)
    dataset_pproc.fillna(method="ffill", inplace=True)
    dataset_pproc.interpolate(method="linear", axis=0)

    return dataset_pproc


def get_dataset_from_series(dataset_pproc, n_hours):
    """
    Transform the temporal series to a dataset
    - dataset_pproc is the input temporal series dataset
    - n_hours specify the number of lag hours
    """
    # obtenemos los valores como una matriz
    values = dataset_pproc.values
    # ensure all data is float
    values = values.astype("float32")
    # normalize features
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(values)
    scaled = pd.DataFrame(
        scaled, columns=dataset_pproc.columns
    )  # frame as supervised learning

    reframed = series_to_supervised(scaled, n_hours, 1)
    return reframed, scaler
