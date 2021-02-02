import sympy
import numpy as np
import json
import pyDHE

class FLServerHelper:
	encrypted_suvs_clientwise = {}
	def __init__(self):
		print("fl_server object made")

	def pass_model_parameters(self):
		parameters = "parameters"
		return parameters

	#reset the encrypted suvs dict
	def deleteVal(self):
		self.encrypted_suvs_clientwise = {}

	def weights_from_json(self, model_weights_json):
		json_load = json.loads(model_weights_json)
		model_weights_list = np.array(json_load)
		model_weights = []
		for i in model_weights_list:
			model_weights.append(np.array(i,dtype=np.float32))
		return model_weights

	#average the received updates
	def averaging(self, updates, count_clients):
		for key, value in updates.items():
			updates[key] = self.weights_from_json(value) #convert back from json
		sum_updates = []
		#initializing
		for key, value in updates.items():
			for item in value:
				sum_updates.append(np.zeros_like(item))
			break
		#add all received updates from updates dict
		for key, value in updates.items():
			for i in range(0, len(value)):
				sum_updates[i] = np.add(sum_updates[i], value[i])
		#average the summed updates
		for i in range(0, len(sum_updates)):
			sum_updates[i] = sum_updates[i] / count_clients
		#delete old suvs
		self.deleteVal()
		return sum_updates

	#each entry in dict holds the suv dict created by one client for others
	#reorder it for the server to send suvs from all clients for each client
	def perturb_util1(self, dict):
		for key, value in dict.items():
			self.encrypted_suvs_clientwise[key] = {}
		for key, value in dict.items():
			for key_in, value_in in value.items():
				if(key != key_in):
					self.encrypted_suvs_clientwise[key_in][key] = value_in
		return self.encrypted_suvs_clientwise
