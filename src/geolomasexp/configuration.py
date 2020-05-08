# -*- coding: utf-8 -*-
"""
	Util functions and classes to configure scripts and experiments
"""

import json
import logging
import pandas as pd
import sys


from geolomasexp import __version__

__author__ = "Leandro Abraham"
__copyright__ = "Leandro Abraham"
__license__ = "mit"

# _logger = logging.getLogger(__name__)
# logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
# loglevel = logging.DEBUG
# logging.basicConfig(level=loglevel, stream=sys.stdout,format=logformat, datefmt="%Y-%m-%d %H:%M:%S")

"""
	Class that represents a training run configuration
	TO DO : no parsear, directamente en el archivo configuracion tener variables tipadas
"""
class TrainingScriptConfig(object):

	config_file_path = ''
	input_csv = ''
	output_log_file = 'training.log'
	output_models_path = 'models/'
	output_results_path = 'results/'
	early_stop_patience=10
	epochs=5
	model_loss=''
	optimizer=''
	config_data = None


	def __init__(self,config_file_path):

		if config_file_path :
			self.config_file_path = config_file_path


			with open(self.config_file_path) as json_data_file:
				self.config_data = json.load(json_data_file)
			# leer atributos comunes de archivo de configuracion
			self.input_csv = self.config_data['input_csv']
			self.output_log_file = self.config_data['output_log_file']
			self.output_models_path = self.config_data['output_models_path']
			self.output_results_path = self.config_data['output_results_path']
			self.early_stop_patience = self.config_data['early_stop_patience']
			self.epochs = self.config_data['epochs']
			self.model_loss = self.config_data['model_loss']
			self.optimizer = self.config_data['optimizer']

	def __str__(self):
		return 'esp:{}_eps:{}_loss:{}_opt:{}'.format(
			self.early_stop_patience,
			self.epochs,
			self.model_loss,
			self.optimizer
			)


class LSTMTrainingScriptConfig(TrainingScriptConfig):

	n_past_steps = 5
	date_col = 'date'
	hr_col = 'hr'
	numeric_var = 'temp'
	sensor_var = 'inme'
	target_sensor = 'A620'
	base_config = None
	mid_layers_config = None

	def __init__(self,config_file_path):

		if config_file_path:
			# llamar al super
			TrainingScriptConfig.__init__(self,config_file_path)
			# leer atributos especificos de lstm de archivo de configuracion
			self.n_past_steps = self.config_data['n_past_steps']
			self.date_col = self.config_data['date_col']
			self.hr_col = self.config_data['hr_col']
			self.numeric_var = self.config_data['numeric_var']
			self.sensor_var = self.config_data['sensor_var']
			self.target_sensor = self.config_data['target_sensor']
			self.base_config = self.config_data['base_config']
			self.mid_layers_config = self.config_data['mid_layers_config']

	def __str__(self):
		super_str = TrainingScriptConfig.__str__(self)

		base_conf_str = self.base_config['first_layer']['mult']+self.base_config['first_layer']['dropout_rate']+self.base_config['last_layer']['mult']+self.base_config['last_layer']['dropout_rate']

		mid_conf_str = self.mid_layers_config['n_layers']+self.mid_layers_config['mult']+self.mid_layers_config['dropout_rate']

		return '{}_pstps:{}_sensor:{}_var:{}_basenet:{}_midnet:{}'.format(
			super_str,
			self.n_past_steps,
			self.target_sensor,
			self.numeric_var,
			base_conf_str,
			mid_conf_str
			)

class LSTMHyperoptTrainingScriptConfig(LSTMTrainingScriptConfig):

	hyperopt_pars = None

	def __init__(self,config_file_path):

		if config_file_path:
			# llamar al super
			LSTMTrainingScriptConfig.__init__(self,config_file_path)
			# leer atributos especificos de lstm hyperopt de archivo de configuracion
			self.hyperopt_pars = self.config_data['hyperopt_pars']

	def __str__(self):
		super_str = LSTMTrainingScriptConfig.__str__(self)

		hyperopt_pars_str = str(self.hyperopt_pars['mid_layers'])+str(self.hyperopt_pars['mults'])+str(self.hyperopt_pars['dropout_rate_range'])+str(self.hyperopt_pars['max_evals'])

		return '{}_hyperoptpars:{}'.format(
			super_str,
			hyperopt_pars_str
			)
