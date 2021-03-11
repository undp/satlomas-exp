from satlomas import __version__

from hyperopt import Trials, STATUS_OK, tpe
from hyperas import optim
from hyperas.distributions import choice, uniform


import logging
import numpy as np
import pandas as pd
import pickle
import sys

from keras.callbacks import (
	EarlyStopping,
	ModelCheckpoint
)
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


__author__ = "Leandro Abraham"
__copyright__ = "Leandro Abraham"
__license__ = "mit"


def get_lstm_nnet_opt(
	train_X,train_y,val_X,val_y):



	n_input_neurons = train_X.shape[1]


	model = Sequential()
	model.add(
		LSTM(
			choice([2, 3]) * n_input_neurons,
			input_shape=(n_input_neurons, train_X.shape[2]),
			return_sequences=True
			)
		)
	model.add(Dropout(rate={{uniform(0,0.5)}}))


	n_mid_layers = 1
	mid_layers_mult = 3
	for i in range(n_mid_layers):
		model.add(LSTM(mid_layers_mult * n_input_neurons, return_sequences=True))
		model.add(Dropout(rate={{uniform(0,0.5)}}))

	last_layer_mult = 2
	model.add(last_layer_mult * n_input_neurons)
	model.add(Dropout(rate={{uniform(0,0.5)}}))

	model.add(Dense(1))

	model_loss = 'mean_squared_error'

	model.compile(loss=model_loss, metrics=['accuracy'],
				  optimizer={{choice(['rmsprop', 'adam'])}})


	early_stop_patience = 10

	early_stopping = EarlyStopping(
		monitor='val_loss',
		patience=early_stop_patience,
		verbose=1, mode='min',
		restore_best_weights=True)

	time_stmp = datetime.now()

	time_stmp_str = time_stmp.strftime("%Y-%m-%d_%H:%M:%S")

	output_models_path = 'models/'

	out_model_name = '{}_hyperas_model_{}.hdf5'.format(
			output_models_path,
			time_stmp_str)

	history_out_name = '{}_hyperas_history_{}.pickle'.format(
			output_models_path,
			time_stmp_str)

	checkpoint = ModelCheckpoint(
		out_model_name,
		save_best_only=True,
		monitor='val_loss',
		mode='min',verbose=2)


	result = model.fit(
		train_X, train_y,
		batch_size={{choice([64, 128])}},
		epochs=epochs,
		validation_data=(val_X, val_y),
		verbose=1, shuffle=False,callbacks=[checkpoint,early_stopping])

	with open(history_out_name, 'wb') as file_pi:
		pickle.dump(result, file_pi)

	validation_acc = np.amax(result.history['val_acc'])
	print('Best validation acc of epoch:', validation_acc)

	print('Returning saved model {}'.format(out_model_name))
	model = load_model(out_model_name)
	return {'loss': -validation_acc, 'status': STATUS_OK, 'model': model}
