import engineio
import eventlet
eventlet.monkey_patch()
import socketio
import time
import json
import numpy as np
import pyDHE
import modelstruct
from flserverhelper import FLServerHelper
import pandas as pd
from keras.models import model_from_json

NO_OF_ROUNDS = 2

sio = socketio.Server(async_mode='eventlet')
app = socketio.Middleware(sio)

Bob = pyDHE.new(18)
pkey = Bob.getPublicKey()

count_clients = 0
count_rounds = 0
count_auth_clients = 0
client_threshold  = 3
update_threshold = 3
updates_received = 0
client_updates = {}
server_wait_time = 5
suv_dictionary = {}
count_train_done = 0
count_shared_done = 0
fin_weights_str = retry.model_weights_json #initialized weights
fin_struct = retry.model_json #initialized model structure

fin_weights = []
credentials=[{'username':'$un@in@','password':'passit'},{'username':'priya','password':'priy@'}]
shared_keys = {}
fl_server_helper = FLServerHelper()

pub_keys = {}

#keeps track of number of connected clients
@sio.on('connect')
def connect(sid, environ):
    global count_clients
    count_clients+=1
    print('connect')
    client_updates[sid] = "" #initializing dict for client update with key as sid of client

#authentication
#todo: add a stronger authentication mechanism
@sio.on('authenticate')
def authenticate(sid, dict):
    global credentials, count_auth_clients
    found = False
    for item in credentials:
        if dict['username'] == item['username']:
            found = True
            if dict['password'] != item['password']:
                sio.disconnect(sid)
            else:
                print('connection authenticated')
                count_auth_clients+=1
                break
    if found == False: #if unknown user, disconnect
        sio.disconnect(sid)

@sio.on('message')
def message(sid, data):
    print('message ', data)

#keeps track of disconnecting clients
@sio.on('disconnect')
def disconnect(sid):
    global count_clients
    count_clients-=1
    client_updates.pop(sid)
    print('disconnect', sid)

#keeps track of updates received from clients
@sio.on('get_updates')
def get_updates(sid, update):
    global updates_received, client_updates
    updates_received += 1
    client_updates[sid] = update

@sio.on('receive_public_key')
def receive_public_key(sid, pkey):
    global pub_keys
    pub_keys[sid] = pkey #receive and store the public key of each client to share with other clients

@sio.on('receive_perturb')
def receive_perturb(sid,suv_dict):
    global suv_dictionary
    #save the received suvs dict for each client
    suv_dictionary[sid] = suv_dict

#keeps track of number of clients which have completed training
@sio.on('training_status')
def training_status(sid, data):
    global count_train_done
    count_train_done+=1
    print("train status: " + data)
    #secure_agg()

#keeps track of number of clients done with shared key generation
@sio.on('shared_key_status')
def shared_key_status(sid, data):
    global count_shared_done
    count_shared_done+=1
    print("shared status: "+ data)

#server listening on 8004 port for connections from clients
def connServ():
    eventlet.wsgi.server(eventlet.listen(('', 8004)), app)

def send_model():
    global count_clients, client_threshold, count_train_done, fin_weights, fin_weights_str, count_auth_clients
    #atleast client_threshold authenticated clients should be connected
    if count_clients >= client_threshold and count_clients == count_auth_clients:
        print('threshold reached')
        #emit the model structure and weights to clients
        sio.emit('receive_model', '{"structure" : ' + fin_struct + ', "weights" : ' + fin_weights_str + '}')
        fin_weights = fl_server_helper.weights_from_json(fin_weights_str)
        #wait for all clients to finish training
        while count_train_done < count_clients:
            eventlet.greenthread.sleep(seconds=5)
        return True
    return False

def diffie_hellman():
    global pub_keys, count_shared_done
    sio.emit('get_public_keys','send me public keys')

    #wait for all clients to send their x keys
    while len(pub_keys)<count_clients:
        eventlet.greenthread.sleep(seconds=5)
    #send the aggregated x keys to all clients
    sio.emit('receive_pub_keys',pub_keys)

    #wait for connected clients to send shared key update
    while count_shared_done < count_clients:
        eventlet.greenthread.sleep(seconds=5)


def secure_agg():
    global count_clients, suv_dictionary
    print("Inside secure aggregation")
    diffie_hellman()
    #ping the clients for suvs
    sio.emit('send_perturbs','Send me the perturbations')
    #wait for all connected clients to send suv dict
    while len(suv_dictionary) < count_clients:
        eventlet.greenthread.sleep(seconds=5)

    #get encrypted suvs dict from all clients to each client
    encrypted_suv_clientwise = fl_server_helper.perturb_util1(suv_dictionary)
    for key, values in encrypted_suv_clientwise.items():
        sio.emit('receive_suvs',values,room=key) #emit the dict to respective clients based on key



def federating_process():
    global count_clients, updates_received, update_threshold, client_updates, suv_dictionary, fin_weights, fin_weights_str, count_rounds
    while count_rounds<NO_OF_ROUNDS:
        print("round no: #" + str(count_rounds))
        eventlet.greenthread.sleep(seconds=5)
        if  send_model(): #if all clients have sent info about completed training
            #get the masked updates from all clients
            secure_agg()
            #wait for all clients to send updates
            while updates_received < count_clients:
                eventlet.greenthread.sleep(seconds=5)

            sum_updates = fl_server_helper.averaging(client_updates, count_clients)
            for i in range(0,len(sum_updates)):
                # print(fin_weights[i].shape)
                # print(sum_updates[i].shape)
                # add the averaged weights from clients with current model weights
                fin_weights[i] = np.add(fin_weights[i],sum_updates[i])
            #convert to json for next round  of transmission
            fin_weights_str = pd.Series(fin_weights).to_json(orient='values')
            sio.emit('clear_round','Clear the round rn') #notify the client of successful round to clear the round data

            #server resetting its variables for next round
            for key, value in client_updates.items():
                client_updates[key] = ""
            updates_received = 0
            suv_dictionary = {}
            count_train_done = 0
            count_shared_done = 0
            count_rounds += 1
            print("-------------------------------------------ROUND COMPLETED-----------------------------------------------------------------------------")

    print("ALL ROUNDS DONE")
    #save the final model on servers end
    modelfile = open('model','w')
    modelfile.write(fin_weights_str)
    modelfile.close()
    model_string = '{"structure" : ' + fin_struct + ', "weights" : ' + fin_weights_str + '}'
    dict = json.loads(model_string)
    model_tosave = model_from_json(json.dumps(dict["structure"]))
    model_weights_tosave = weights_from_json(json.dumps(dict["weights"]))
    model_tosave.set_weights(model_weights_tosave)
    model_tosave.save('model.h5')
    #sending final model to client
    sio.emit('receive_averaged_model','{"structure" : ' + fin_struct + ', "weights" : ' + fin_weights_str + '}')




if __name__ == '__main__':
    pool = eventlet.GreenPool()
    pool.spawn(connServ) #spawn threads as connections are received from clients
    pool.spawn(federating_process) #call federating_process for each client
    pool.waitall() #wait for all clients to finish
