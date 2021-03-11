# -*- coding: utf-8 -*-
"""
This is a script to train an LSTM neural network to predict temporal series.
To run this script :
python src/satlomas/train_lstm.py config_train_lstm_temp.json -vv

"""

import argparse
import os
import logging
import time
import pandas as pd
import pickle
import sys

from datetime import datetime
from satlomas import __version__
from satlomas.configuration import LSTMTrainingScriptConfig
from satlomas.data import read_time_series_from_csv
from satlomas.feature import (
    get_dataset_from_series,
    get_interest_variable
)
from satlomas.model import (
    build_lstm_nnet,
    eval_regression_performance,
    fit_model,
    train_val_test_split
)

from sklearn.metrics import mean_absolute_error,r2_score

__author__ = "Leandro Abraham"
__copyright__ = "Dymaxion Labs"
__license__ = "apache-2.0"

_logger = logging.getLogger(__name__)



def train_lstm(script_config):
    """Function to train an LSTM neural network looking at the past

    Args:
      n_steps_past (int): integer

    Returns: TO DO
      int: n-th Fibonacci number
    """

    time_stmp = datetime.now()

    time_stmp_str = time_stmp.strftime("%Y-%m-%d_%H:%M:%S")

    n_past_steps = script_config.n_past_steps
    input_csv = script_config.input_csv
    _logger.debug("using {} steps in the past".format(n_past_steps))
    _logger.debug("using {} input dataset".format(input_csv))


    date_col = script_config.date_col
    hr_col = script_config.hr_col
    numeric_var = script_config.numeric_var
    sensor_var = script_config.sensor_var
    target_sensor = script_config.target_sensor
    output_models_path = script_config.output_models_path
    output_results_path = script_config.output_results_path

    base_config = script_config.base_config
    mid_layers_config = script_config.mid_layers_config
    model_loss = script_config.model_loss
    optimizer = script_config.optimizer

    early_stop_patience=script_config.early_stop_patience
    epochs=script_config.epochs

    # Leer el dataset
    raw_dataset = read_time_series_from_csv(input_csv,date_col,hr_col,numeric_var,sensor_var)
    _logger.debug("Dataset of shape {} read".format(raw_dataset.shape))

    # Obtener la variable de interes del dataset
    time_series_dset = get_interest_variable(raw_dataset,sensor_var,date_col,hr_col,numeric_var,target_sensor)
    _logger.debug("Got time series dataset of shape {} with columns {}".format(time_series_dset.shape,time_series_dset.columns))

    sup_dataset,scaler = get_dataset_from_series(time_series_dset,n_past_steps)
    _logger.debug("Got supervised dataset of shape {} with columns {}".format(sup_dataset.shape,sup_dataset.columns))

    # guardar el objeto scaler
    with open('{}{}_scaler_{}.pickle'.format(
        output_models_path,
        str(script_config),
        time_stmp_str), 'wb') as file_pi:
        pickle.dump(scaler, file_pi)

    n_features = time_series_dset.shape[1]
    dataset_splits = train_val_test_split(sup_dataset,n_past_steps,n_features,numeric_var)
    _logger.debug("Got split:")
    for key in dataset_splits.keys():
        _logger.debug("{} shapes: {},{}".format(key,dataset_splits[key]['X'].shape,dataset_splits[key]['y'].shape))


    trainset = dataset_splits['trainset']
    lstm_nnet = build_lstm_nnet(trainset['X'],base_config,mid_layers_config,model_loss,optimizer)
    _logger.debug("Got LSTM NNet {}".format(lstm_nnet))

    out_model_name = '{}{}_model_{}.hdf5'.format(
        output_models_path,
        str(script_config),
        time_stmp_str)

    history_out_name = '{}{}_history_{}.pickle'.format(
        output_models_path,
        str(script_config),
        time_stmp_str)

    tic = time.time()
    lstm_nnet = fit_model(
        lstm_nnet,
        trainset,
        dataset_splits['valset'],
        target_sensor,
        numeric_var,
        output_models_path,
        early_stop_patience,
        epochs,
        time_stmp_str,
        out_model_name,
        history_out_name
    )
    train_time = time.time() - tic
    _logger.debug("Trained LSTM NNet {} took {} seconds for {} datapoints".format(
        lstm_nnet,train_time,trainset['X'].shape[0]))

    tic = time.time()
    train_mae = eval_regression_performance(trainset,lstm_nnet,scaler,measure = mean_absolute_error)
    train_eval_time = time.time() - tic
    _logger.debug("Train MAE {} and took {} seconds".format(train_mae,train_eval_time))

    tic = time.time()
    test_mae = eval_regression_performance(dataset_splits['testset'],lstm_nnet,scaler, measure = mean_absolute_error)
    test_eval_time = time.time() - tic
    _logger.debug("Test MAE {} and took {} seconds".format(test_mae,test_eval_time))

    train_r2 = eval_regression_performance(trainset,lstm_nnet,scaler,measure = r2_score)
    _logger.debug("Train R2 {}".format(train_r2))

    test_r2 = eval_regression_performance(dataset_splits['testset'],lstm_nnet,scaler, measure = r2_score)
    _logger.debug("Test R2 {}".format(test_r2))


    # Saving the training result
    results = pd.DataFrame({
            'sensor':[target_sensor],
            'target_variable':[numeric_var],
            'base_nnet_config':[base_config],
            'mid_layers_config':[mid_layers_config],
            'model_loss':[model_loss],
            'optimizer':[optimizer],
            'early_stop_patience':[early_stop_patience],
            'epochs':[epochs],
            'train_mae':[train_mae],
            'test_mae':[test_mae],
            'train_r2':[train_r2],
            'test_r2':[test_r2],
            'train_time':[train_time],
            'train_eval_time':[train_eval_time],
            'test_eval_time':[test_eval_time],
            'trainset_size':[trainset['X'].shape[0]]
        }
        )



    results.to_csv(
        '{}{}_results_{}.csv'.format(
            output_results_path,
            str(script_config),
            time_stmp_str),
        index=False
        )

    # Empaquetamos modelo, scaler y mae en un objeto para usar al predecir
    model_package = {'model':lstm_nnet,'scaler':scaler,'test_mae':test_mae}

    with open('{}{}_model_package_{}.model'.format(
        output_models_path,
        str(script_config),
        time_stmp_str), 'wb') as file_pi:
        pickle.dump(model_package, file_pi)

def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="Train an LSTM neural network to predict the next step of a time series based on the past")
    parser.add_argument(
        "--version",
        action="version",
        version="satlomas {ver}".format(ver=__version__))
    parser.add_argument(
        dest="config_file",
        help="Input configuration json file",
        type=str,
        metavar="STR")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO)
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG)
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    script_config = LSTMTrainingScriptConfig(args.config_file)
    _logger.debug("Starting training an LSTM with {} configuration".format(args.config_file))


    if not os.path.exists(script_config.output_models_path):
        os.makedirs(script_config.output_models_path)

    if not os.path.exists(script_config.output_results_path):
        os.makedirs(script_config.output_results_path)


    tic = time.time()
    train_lstm(script_config)
    toc = time.time()

    _logger.debug("Training has ended, took {} seconds overall".format(toc-tic))


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
