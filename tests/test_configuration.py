# -*- coding: utf-8 -*-

import pytest
from satlomasproc.configuration import LSTMTrainingScriptConfig, TrainingScriptConfig

__author__ = "Leandro Abraham"
__copyright__ = "Dymaxion Labs"
__license__ = "apache-2.0"


# Mock and test constants
EARLY_STOP_PATIENCE = 77
EPOCHS = 7
MODEL_LOSS = "mean_squared_error"
OPTIMIZER = "adam"
PAST_STEPS = 5
NUMERIC_VAR = "temp"
SENSOR = "A620"
BASE_CONFIG = {
    "first_layer": {"mult": 2, "dropout_rate": 0.2},
    "last_layer": {"mult": 2, "dropout_rate": 0.2},
}
MID_CONFIG = {"n_layers": 2, "mult": 2, "dropout_rate": 0.2}


def get_configuration_mock():

    script_config = TrainingScriptConfig(None)
    script_config.early_stop_patience = EARLY_STOP_PATIENCE
    script_config.epochs = EPOCHS
    script_config.model_loss = MODEL_LOSS
    script_config.optimizer = OPTIMIZER

    return script_config


def get_lstm_configuration_mock():

    script_config = LSTMTrainingScriptConfig(None)
    script_config.early_stop_patience = EARLY_STOP_PATIENCE
    script_config.epochs = EPOCHS
    script_config.model_loss = MODEL_LOSS
    script_config.optimizer = OPTIMIZER
    script_config.n_past_steps = PAST_STEPS
    script_config.numeric_var = NUMERIC_VAR
    script_config.target_sensor = SENSOR
    script_config.base_config = BASE_CONFIG
    script_config.mid_layers_config = MID_CONFIG

    return script_config


# Test str_method of base script configuration
def test_script_configuration_str():

    script_config = get_configuration_mock()

    get_configuration_mock_str = str(script_config)

    expected_str = "esp:{}_eps:{}_loss:{}_opt:{}".format(
        EARLY_STOP_PATIENCE, EPOCHS, MODEL_LOSS, OPTIMIZER
    )

    assert get_configuration_mock_str == expected_str


# Test str_method of LSTM script configuration
def test_lstm_script_configuration_str():

    script_config = get_lstm_configuration_mock()

    get_configuration_mock_str = str(script_config)

    expected_str = "esp:{}_eps:{}_loss:{}_opt:{}_pstps:{}_sensor:{}_var:{}_basenet:{}_midnet:{}".format(
        EARLY_STOP_PATIENCE,
        EPOCHS,
        MODEL_LOSS,
        OPTIMIZER,
        PAST_STEPS,
        SENSOR,
        NUMERIC_VAR,
        BASE_CONFIG,
        MID_CONFIG,
    )

    assert get_configuration_mock_str == expected_str
