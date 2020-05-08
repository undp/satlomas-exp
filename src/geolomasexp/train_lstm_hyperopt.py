# -*- coding: utf-8 -*-
"""
This is a script to train an LSTM neural network to predict temporal series.
To run this script :
python src/geolomas/train_lstm_hyperopt.py config_train_lstm_temp.json -vv

"""

import argparse
import os
import logging
import time
import pandas as pd
import pickle
import sys

from datetime import datetime
from geolomasexp import __version__
from geolomasexp.configuration import LSTMHyperoptTrainingScriptConfig
from geolomasexp.data import read_time_series_from_csv
from geolomasexp.feature import (
    get_dataset_from_series,
    get_interest_variable
)

from geolomasexp.model import (
    build_lstm_nnet,
    eval_regression_performance,
    fit_model,
    train_val_test_split
)
from geolomasexp.model_hyperopt import (
    get_lstm_nnet_opt
)
from hyperopt import (
    tpe,
    hp,
    fmin
)
from keras.models import load_model
from sklearn.metrics import mean_absolute_error,r2_score

from stations.models import Measurement, Place, Station

__author__ = "Leandro Abraham"
__copyright__ = "Leandro Abraham"
__license__ = "mit"

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

    hyperopt_pars = script_config.hyperopt_pars

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
    with open('{}{}_hyperopt_scaler_{}.pickle'.format(
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

    out_model_name = '{}{}_hyperopt_model_{}.hdf5'.format(
        output_models_path,
        str(script_config),
        time_stmp_str)

    history_out_name = '{}{}_hyperopt_history_{}.pickle'.format(
        output_models_path,
        str(script_config),
        time_stmp_str)

    mults = hyperopt_pars['mults']
    dropout_rate_range = hyperopt_pars['dropout_rate_range']
    n_mid_layers = hyperopt_pars['mid_layers']

    _logger.debug("LSTM NNNet hyperpars to optimize on: mults:{}, dropout:{}, n mid layers:{}".format(
        mults,dropout_rate_range,n_mid_layers))

    tic = time.time()
    space = hp.choice('nnet_config',[
        {'dataset_splits': dataset_splits,
         'mult_1': hp.choice('mult_1',mults),
         'dropout_rate_1' : hp.uniform('dropout_rate_1',
                                    dropout_rate_range[0],
                                    dropout_rate_range[1]),
         'mult_mid': hp.choice('mult_mid',mults),
         'dropout_rate_mid' : hp.uniform('dropout_rate_mid',
                                    dropout_rate_range[0],
                                    dropout_rate_range[1]),
         'mult_n': hp.choice('mult_n',mults),
         'dropout_rate_n' : hp.uniform('dropout_rate_n',
                                    dropout_rate_range[0],
                                    dropout_rate_range[1]),
         'n_mid_layers': hp.choice('n_mid_layers',n_mid_layers),
         'model_loss' : model_loss,
         'optimizer' : optimizer,
         'target_var' : numeric_var,
         'output_models_path' : output_models_path,
         'early_stop_patience': early_stop_patience,
         'epochs' : epochs,
         'time_stmp_str' : time_stmp_str,
         'out_model_name' : out_model_name,
         'history_out_name' : history_out_name
        }
        ])

    optimal_pars = fmin(get_lstm_nnet_opt,space,algo=tpe.suggest,max_evals=hyperopt_pars['max_evals'])

    opt_time = time.time() - tic
    _logger.debug("Hyper parameter optimization for optimal pars {} took {} seconds for {} datapoints".format(
        optimal_pars,opt_time,trainset['X'].shape[0]))


    # guardando hyper parameters
    with open('{}{}_hyperopt_optimal_pars_{}.pickle'.format(
        output_models_path,
        str(script_config),
        time_stmp_str), 'wb') as file_pi:
        pickle.dump(optimal_pars, file_pi)

    # read the model from disk ?
    #lstm_nnet = load_model(out_model_name)
    #_logger.debug("Got LSTM NNet from disk {}".format(lstm_nnet))

    #no estoy seguro que sea necesario, pero deberiamos construir una red nueva con los parametros elegidos pot hyperopt
    base_config_opt = {
        "first_layer":{
            "mult":int(mults[optimal_pars['mult_1']]),
            "dropout_rate":float(optimal_pars['dropout_rate_1'])
            #"dropout_range":[0,1]
            },
        "last_layer":{
            "mult":int(mults[optimal_pars['mult_n']]),
            "dropout_rate":float(optimal_pars['dropout_rate_n'])
            #"dropout_range":[0,1]
            }
    }
    mid_layers_config_opt = {
        "n_layers":int(n_mid_layers[optimal_pars['n_mid_layers']]),
        "mult":int(mults[optimal_pars['mult_mid']]),
        "dropout_rate":float(optimal_pars['dropout_rate_mid'])
        #"dropout_range":[0,1]
        }

    lstm_nnet_arq = build_lstm_nnet(trainset['X'],base_config_opt,mid_layers_config_opt,model_loss,optimizer)
    _logger.debug("Build LSTM NNet with optimal parameters \n {}".format(lstm_nnet_arq.summary()))


    #recien aqui entrenamos con todo el dataset y la arquitectura optima
    tic = time.time()
    lstm_nnet = fit_model(
        lstm_nnet_arq,
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
            'hyperopt_pars':[hyperopt_pars],
            'optimal_pars':[optimal_pars],
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
        '{}{}_hyperopt_results_{}.csv'.format(
            output_results_path,
            str(script_config),
            time_stmp_str),
        index=False
        )

    # Empaquetamos modelo, scaler y mae en un objeto para usar al predecir
    model_package = {'model':lstm_nnet,'scaler':scaler,'test_mae':test_mae,'optimal_pars':optimal_pars}

    with open('{}{}_model_hyperopt_package_{}.model'.format(
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
        version="geolomas {ver}".format(ver=__version__))
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
    script_config = LSTMHyperoptTrainingScriptConfig(args.config_file)
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
