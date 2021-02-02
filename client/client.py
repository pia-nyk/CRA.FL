import socketio
import json
import pyDHE
import time
from pymemcache.client import base
#import logging as log
from secure_aggregation import SecureAggregation
from flclienthelper import FLClientHelper
from keras import backend as K
from keras.models import model_from_json
import tensorflow as tf

#using memcached for storing login creds and state of the client
sio = socketio.Client()

fl_client_helper = None
sa_client = SecureAggregation()

#memcached server config
mem_client = base.Client(('localhost', 11211))

#initializing memcached hashset
mem_client.set('connection',"Connection not established")
mem_client.set('model_parameters',"Waiting for others to connect")
mem_client.set('training_status',"Training Received Model on Local Data")
mem_client.set('updates_status',"Federated Averaging in Process")
mem_client.set('clear_round_success','Server averaging the updates')
mem_client.set('username',"")
mem_client.set('password',"")
mem_client.set('model','')

var = 0
dhe_helper = None
x = None
credentials = {}
updates = []


@sio.on('connect')
def on_connect():
	global dhe_helper, x, Alice_server, pkey_server, credentials

	#diffie hellman keys between each pair of participating clients
	#more info on pyDHE module - https://github.com/deadPix3l/pyDHE
	dhe_helper = pyDHE.new()

	# x = G^a mod P
	x = dhe_helper.getPublicKey() #public key - generated using common public key and own private key
	#keep on waiting till login credentials are received
	while not mem_client.get('username') or not mem_client.get('password'):
		time.sleep(5)
		#continue
	print(' connection established ')
	credentials['username'] = mem_client.get('username').decode('utf-8')
	credentials['password'] = mem_client.get('password').decode('utf-8')

	#only authorized clients are able to access the main model
	sio.emit('authenticate', credentials)
	mem_client.set('connection',"Connection Successfully Established")

#if final averaged model weights are received, disconnect from server
@sio.on('receive_averaged_model')
def receive_averaged_model(model_string):
	mem_client.set('model',model_string) #set the model in cache
	sio.emit('disconnect')

#if data gets received from server to clients
@sio.on('message')
def on_message(data):
	print(' data received at client ' + data)
	sio.emit('message','This message has been successfully received')

@sio.on('disconnect')
def on_disconnect():
	#reset memcached hashset
	global credentials
	credentials['username'] = None
	credentials['password'] = None
	mem_client.set('connection',"Connection not established")
	mem_client.set('model_parameters',"Waiting for model to be received")
	mem_client.set('training_status',"Training Received Model on Local Data")
	mem_client.set('updates_status',"Federated Averaging in Process")
	mem_client.set('clear_round_success','Server averaging the updates')
	print(' disconnected from server ')

#server pinging for model updates from client
@sio.on('send_perturbs')
def on_send_perturbs(data):
	global updates
	print(data)

	#if training is not completed, updates arent still filled, wait
	while not updates:
		time.sleep(5)
	#get encrypted suvs list with all other participants - from this client to all other clients
	suv_dict = sa_client.encryption(updates)
	sio.emit('receive_perturb',suv_dict) #send the dict of suvs for all clients to the server for distribution

@sio.on('wait_shared_key')
def on_wait_shared_key(data):

	skey = sa_client.get_shared_key_length()
	while(skey < data):
		time.sleep(5)
		skey = sa_client.get_shared_key_length()

#receive x keys of all other participants from the server
#each client has N-1 keys
#dictionary received from server
@sio.on('receive_pub_keys')
def receive_pub_keys(pub_keys):
	global dhe_helper
	print("Received public keys")
	shared_keys_generated = False
	shared_keys_generated = sa_client.receive_pub_keys(pub_keys, dhe_helper)

	#if shared keys are generated, ping server for its tracking
	if shared_keys_generated:
		sio.emit('shared_key_status','shared keys made')

@sio.on('get_public_keys')
def on_get_public_keys(data):
	global x
	sio.emit('receive_public_key',x) #once notified by the server, send own public key to server for distributing across all clients

#servers notification on round complete
@sio.on('clear_round')
def on_clear_round(data):
	#resetting all variables
	global updates
	updates = []
	sa_client.deleteVal()
	mem_client.set('model_parameters',"Waiting for model to be received")
	mem_client.set('training_status',"Training Received Model on Local Data")
	mem_client.set('updates_status',"Federated Averaging in Process")
	mem_client.set('clear_round_success','Round completed')


@sio.on('receive_model')
def on_receive_model(model_json):
	global updates, count
	mem_client.set('model_parameters',"Model downloaded successfully") #save state in memcached
	fl_client_helper = FLClientHelper()
	#update local model
	fl_client_helper.preprocess_data(model_json)
	#train the received model on the local data
	updates = fl_client_helper.train_model(model_weights)
	mem_client.set('training_status',"Training completed successfully") #save training state in memcached
	sio.emit('training_status','training done') #ping server regarding training complete
	print(' sending updates to server ')
	K.clear_session()

#receive the encrypted suvs from all other clients
@sio.on('receive_suvs')
def on_receive_suvs(encrypted_suv_clientwise):
	sa_client.decryption(encrypted_suv_clientwise) #decrypt the suvs using pairwise diffie hellman received earlier
	sio.emit('get_updates', sa_client.create_update()) #transmit masked updates to server
	mem_client.set('updates_status',"Updates sent back to server successfully") #save the state in memcached


sio.connect('http://192.168.43.248:8004') #server ip
