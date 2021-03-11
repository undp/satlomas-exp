# -*- coding: utf-8 -*-
"""
	Util functions to build, train and evaluate models
"""
from satlomas import __version__

from keras.layers import (
	Dense,
	Dropout,
	LSTM
)
from keras.models import (
	load_model,
	model_from_json,
	Sequential
)
from sklearn.metrics import mean_absolute_error

from satlomas.model import fit_model

import logging
import numpy as np
import pandas as pd
import pickle
import sys




__author__ = "Leandro Abraham"
__copyright__ = "Leandro Abraham"
__license__ = "mit"


"""
	Build and train an LSTM neural network considering the parameters and returns a value to optimize through hyperopt
	TO DO :
	- documentar mejor
"""
def get_lstm_nnet_opt(args):


	dataset_splits = args['dataset_splits']

	X = dataset_splits['trainset']['X']
	y = dataset_splits['trainset']['y']


	n_input_neurons = X.shape[1]

	mult_1 = args['mult_1']
	mult_mid = args['mult_mid']
	mult_n = args['mult_n']

	dropout_rate_1 = args['dropout_rate_1']
	dropout_rate_mid = args['dropout_rate_mid']
	dropout_rate_n = args['dropout_rate_n']

	n_mid_layers= args['n_mid_layers']
	model_loss = args['model_loss']
	optimizer = args['optimizer']


	model = Sequential()
	model.add(
		LSTM(
			mult_1 * n_input_neurons,
			input_shape=(n_input_neurons, X.shape[2]),
			return_sequences=True
			)
		)

	model.add(Dropout(rate=dropout_rate_1))



	for i in range(n_mid_layers):
		model.add(LSTM(mult_mid * n_input_neurons, return_sequences=True))
		model.add(Dropout(rate=dropout_rate_mid))

	model.add(LSTM(mult_n * n_input_neurons))
	model.add(Dropout(rate=dropout_rate_n))

	model.add(Dense(1))

	model.compile(loss=model_loss, optimizer=optimizer)

	target_var = args['target_var']
	output_models_path = args['output_models_path']
	early_stop_patience = args['early_stop_patience']
	epochs = args['epochs']
	time_stmp_str = args['time_stmp_str']
	out_model_name = args['out_model_name']
	history_out_name = args['history_out_name']


	# TODO este no deberia salvar modelos intermedios?
	fitted_model = fit_model(model,
							dataset_splits['trainset'],dataset_splits['valset'],
							None,target_var,
							output_models_path,
							early_stop_patience,epochs,
							time_stmp_str,out_model_name,history_out_name)


	with open(history_out_name, 'rb') as file_pi:
		result = pickle.load( file_pi)

	#get the highest validation accuracy of the training epochs
	validation_loss = np.amin(result.history['val_loss'])
	print('Best validation loss of epoch:', validation_loss)

	return validation_loss
