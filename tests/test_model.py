# -*- coding: utf-8 -*-

import numpy as np
import pytest
import glob
from satlomas.model import *
from satlomas.configuration import LSTMTrainingScriptConfig
from keras.models import load_model

__author__ = "Leandro Abraham"
__copyright__ = "Leandro Abraham"
__license__ = "mit"


# to run this test python -m pytest tests/test_model.py

def get_model_package_name():

	model_package_name = glob.glob('models/*_model_package_*.model')[-1]
	print('Using {} packaged model to test'.format(model_package_name))
	
	return model_package_name

def get_model_hyperopt_package_name():

	model_package_name = glob.glob('models/*_model_hyperopt_package_*.model')[-1]
	print('Using {} hyperopt packaged model to test'.format(model_package_name))
	
	return model_package_name



# Test that predictions are returned independently of shape of input datapoint 
def test_predict_with_model_is_not_none():

	model_package_name = get_model_package_name()

	n_past_steps = 3

	#datapoint as array
	#datapoint = np.ones(model.input_shape[1])
	datapoint = np.ones(n_past_steps)

	pred,mae = predict_with_model(datapoint,model_package_name)

	assert pred is not None
	assert mae is not None

	#datapoint as row
	datapoint = np.ones((1,n_past_steps))

	pred,mae = predict_with_model(datapoint,model_package_name)

	assert pred is not None
	assert mae is not None

	#datapoint as column
	datapoint = np.ones((n_past_steps,1))

	pred,mae = predict_with_model(datapoint,model_package_name)

	assert pred is not None
	assert mae is not None


# Test that predictions have expected size and type
def test_predict_with_model_len_type():

	model_package_name = get_model_package_name()

	n_past_steps = 3

	#datapoint as array
	datapoint = np.ones(n_past_steps)

	for steps_future in range(1,35,10):
		preds,mae = predict_with_model(datapoint,model_package_name,steps_future)

		assert len(preds) == steps_future

		preds_as_array = np.array(preds)
		assert any(preds_as_array != None)
		assert str(preds_as_array.dtype) == 'float32'

		assert str(np.dtype(mae)) == 'float32'
		assert mae is not None



# Test that predictions are returned independently of shape of input datapoint 
def test_predict_with_model_is_not_none_hyperopt():

	model_package_name = get_model_hyperopt_package_name()

	n_past_steps = 3

	#datapoint as array
	#datapoint = np.ones(model.input_shape[1])
	datapoint = np.ones(n_past_steps)

	pred,mae = predict_with_model(datapoint,model_package_name)

	assert pred is not None
	assert mae is not None

	#datapoint as row
	datapoint = np.ones((1,n_past_steps))

	pred,mae = predict_with_model(datapoint,model_package_name)

	assert pred is not None
	assert mae is not None

	#datapoint as column
	datapoint = np.ones((n_past_steps,1))

	pred,mae = predict_with_model(datapoint,model_package_name)

	assert pred is not None
	assert mae is not None


# Test that predictions have expected size and type
def test_predict_with_model_len_type_hyperopt():

	model_package_name = get_model_hyperopt_package_name()

	n_past_steps = 3

	#datapoint as array
	datapoint = np.ones(n_past_steps)

	for steps_future in range(1,35,10):
		preds,mae = predict_with_model(datapoint,model_package_name,steps_future)

		assert len(preds) == steps_future

		preds_as_array = np.array(preds)
		assert any(preds_as_array != None)
		assert str(preds_as_array.dtype) == 'float32'

		assert str(np.dtype(mae)) == 'float32'
		assert mae is not None


# TODO : un test que valide que la prediccion sobre un datapoint real este dentro del MAE?
# está bien tener test unitarios pero de calidad?

