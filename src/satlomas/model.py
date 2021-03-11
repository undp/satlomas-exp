# -*- coding: utf-8 -*-
"""
	Util functions to build, train and evaluate models
"""
from satlomas import __version__



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
from sklearn.metrics import mean_absolute_error , max_error , r2_score


__author__ = "Leandro Abraham"
__copyright__ = "Leandro Abraham"
__license__ = "mit"

# _logger = logging.getLogger(__name__)
# logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
# loglevel = logging.DEBUG
# logging.basicConfig(level=loglevel, stream=sys.stdout,format=logformat, datefmt="%Y-%m-%d %H:%M:%S")

def max_error_loss(true,pred):
    return max_error(true,pred)


"""
	Split a dataset into train, validation and test sets
	TO DO : documentar parametros
"""
def train_val_test_split(reframed,n_hours,n_features,target_var = 'temp' ,ascending_sampling = False):

	n_train_hours = int(reframed.shape[0] * 0.6)
	n_val_hours = int(reframed.shape[0] * 0.2)


	if ascending_sampling:
		print("Sampleamos datasets de pasado a futuro")
		train = reframed.iloc[:n_train_hours, :]
		validation = reframed.iloc[n_train_hours:n_train_hours+n_val_hours, :]
		test = reframed.iloc[n_train_hours+n_val_hours:, :]
	else:
		print("Sampleamos datasets de futuro a pasado")
		train = reframed.iloc[-n_train_hours:, :]
		validation = reframed.iloc[-(n_train_hours+n_val_hours):-n_train_hours:, :]
		test = reframed.iloc[:-(n_train_hours+n_val_hours), :]

	# split into input and outputs
	n_obs = n_hours * n_features

	target_col = '{}_t'.format(target_var)
	out_model_name = '{}.hdf5'.format(target_var)
	#target_var = 'prcp(t)'
	train_X, train_y = train.iloc[:, :n_obs].values, train[target_col].values
	val_X, val_y = validation.iloc[:, :n_obs].values, validation[target_col].values
	test_X, test_y = test.iloc[:, :n_obs].values, test[target_col].values
	print(train_X.shape, len(train_X), train_y.shape)

	# reshape input to be 3D [samples, timesteps, features]
	train_X = train_X.reshape((train_X.shape[0], n_hours, n_features))
	val_X = val_X.reshape((val_X.shape[0], n_hours, n_features))
	test_X = test_X.reshape((test_X.shape[0], n_hours, n_features))
	print(train_X.shape, train_y.shape,val_X.shape, val_y.shape, test_X.shape, test_y.shape)

	return {
		'trainset': {'X': train_X,'y': train_y},
		'valset': {'X': val_X,'y': val_y},
		'testset': {'X': test_X,'y': test_y}
	}




"""
	Build an LSTM neural network
	TO DO :
	- documentar mejor
	- directamente pasar el script condfig y sacar todo de ahi
"""
def build_lstm_nnet(
	X,
	base_config,
	mid_layers_config,
	model_loss,
	optimizer):

	n_input_neurons = X.shape[1]


	model = Sequential()
	model.add(
		LSTM(
			base_config['first_layer']['mult'] * n_input_neurons,
			input_shape=(n_input_neurons, X.shape[2]),
			return_sequences=True
			)
		)
	model.add(Dropout(rate=base_config['first_layer']['dropout_rate']))

	for i in range(mid_layers_config['n_layers']):
		model.add(LSTM(mid_layers_config['mult'] * n_input_neurons, return_sequences=True))
		model.add(Dropout(rate=mid_layers_config['dropout_rate']))

	model.add(LSTM(base_config['last_layer']['mult'] * n_input_neurons))
	model.add(Dropout(rate=base_config['last_layer']['dropout_rate']))
	# TO DO : parametrize this
	model.add(Dense(1))
    
	if model_loss == 'max_error' :
		model_loss = max_error_loss
        
	model.compile(loss=model_loss, optimizer=optimizer)

	return model


"""
	Fit a model and save model and results
"""
def fit_model(model,trainset,valset,sensor,target_var,
	output_models_path,early_stop_patience,epochs,time_stmp_str,out_model_name,history_out_name):
	train_X = trainset['X']
	train_y = trainset['y']

	val_X = valset['X']
	val_y = valset['y']


	# fit network
	# que corte despues de no mejorar mucho
	early_stopping = EarlyStopping(
		monitor='val_loss',
		patience=early_stop_patience,
		verbose=1, mode='min',
		restore_best_weights=True)
	# que use el mejor modelo
	checkpoint = ModelCheckpoint(
		out_model_name,
		save_best_only=True,
		monitor='val_loss',
		mode='min',verbose=2)

	history = model.fit(
		train_X, train_y,
		epochs=epochs,
		validation_data=(val_X, val_y),
		verbose=1, shuffle=False,callbacks=[checkpoint,early_stopping])


	with open(history_out_name, 'wb') as file_pi:
		pickle.dump(history, file_pi)

	return load_model(out_model_name)


"""
	Evaluate regression performance for model over dataset
"""
def eval_regression_performance(dset,model,scaler,measure):
	X = dset['X']
	y = dset['y']
	y = y.reshape((len(y), 1))
	yhat = model.predict(X)

	# afecta en algo aplicar invers_stransform sobre una sola columna que con tra la matriz?
	prediction = scaler.inverse_transform(yhat)

	# invert scaling for actual
	true = scaler.inverse_transform(y)

	# calculate MAE
	performance = measure(true, prediction)
	return performance


"""
	Predicts with a model over a re-shaped datapoint
"""
def predict_one_step(X,model_package):
	model = model_package['model']
	scaler = model_package['scaler']
	yhat = model.predict(X)
	return yhat,scaler.inverse_transform(yhat)


"""
	Predict datapoint using model
"""
def predict_with_model(datapoint,model_pckg_filename,future_steps=1):

	with open(model_pckg_filename, 'rb') as file_pi:
		model_package = pickle.load(file_pi)

	model = model_package['model']
	X = np.array(datapoint).reshape(1,model.input_shape[1],model.input_shape[2])
	predictions = []

	try:
		last_pred,last_pred_inv  = predict_one_step(X,model_package)
		predictions.append(last_pred_inv)
	except:
		return None,None

	for steps in range(1,future_steps):
		old = list(X[0,:,0])
		old.append(last_pred)
		X[0,:,0] = np.array(old[1:])
		last_pred,last_pred_inv = predict_one_step(X,model_package)
		predictions.append(last_pred_inv)


	return predictions,model_package['test_mae']
