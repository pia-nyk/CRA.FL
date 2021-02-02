import sympy
import random
import numpy as np
from  numpy import array
import pandas as pd
import json

DATA_FILE_X = "../input/xtrain.csv"
DATA_FILE_Y = "../input/ytrain.csv"
EPOCHS = 5
BATCH_SIZE = 5000

class FLClientHelper:

	def __init__(self):
		#initializing params
		self.model = None
		self.current_model_version = 0
		self.X = pd.read_csv(DATA_FILE_X)
		self.Y = pd.read_csv(DATA_FILE_Y)
		self.updates  = []

	#extract weights from server model and set those to current local model
	def weights_from_json(self,model_weights_json):
		json_load = json.loads(model_weights_json)
		model_weights_list = np.array(json_load)
		model_weights = []
		for i in model_weights_list:
			model_weights.append(np.array(i,dtype=np.float32))
		return model_weights

	#process and store model data received from server
	def preprocess_data(self, data):
		dict = json.loads(model_json)
		model = model_from_json(json.dumps(dict["structure"]))
		self.model = model
		model_weights = fl_client.weights_from_json(json.dumps(dict["weights"]))
		self.model.set_weights(model_weights)

	#training process
	def train_model(self,model_weights):
		print(" start training ")
		self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
		self.model.fit(self.X, self.Y, epochs=EPOCHS, batch_size=BATCH_SIZE)
		self.updates = self.get_updates(model_weights)
		print(" end training ")
		return self.updates

	#get the model updates after training wrt to weights received from server
	def get_updates(self, model_weights):
		print(self.model.get_weights())
		print(model_weights)
		updates =  [(i-j) for (i,j) in zip(self.model.get_weights(),model_weights)]
		print("PRINTING UPDATES:")
		return updates
