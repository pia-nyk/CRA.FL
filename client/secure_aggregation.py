import numpy as np
from numpy import array
import hashlib
import pyaes
import pyDHE
import pandas as pd

'''
    Secure aggregation to ensure, no individual client
    can find about the data of other from the averaged model updates
    or the model structure
'''
class SecureAggregation:
    """docstring for SecureAggregation."""
    R = 1000
    shared_keys={}
    pub_keys = {}
    puvs = {}
    suv = []
    updates  = []
    dhe_helper = None

    def __init__(self):
        print("Secure aggregation object made")

    def get_shared_key_length(self):
        return len(self.shared_keys)

    def generate_shared_key(self):
        #shared keys created for each pair of clients using their x key received from server
        for key, value in self.pub_keys.items():
             #generating the final shared key between each pair of participating clients
            self.shared_keys[key] = self.dhe_helper.update(value)
        return True

    def receive_pub_keys(self, pub_keys, dhe_helper):
        self.pub_keys = pub_keys #saved all clients keys
        self.dhe_helper = dhe_helper
        self.generate_shared_key()

    def encryption(self, updates):
        self.updates = updates
        #randomized suv of use for transmitting updates - dimension depends on updates
        for item in self.updates:
            self.suv.append(np.random.randint(self.R, size=item.shape))
        print("suv")
        print(self.suv)
        #encrypt the suvs - aes using diffie hellman key generated between pair of participants
        encrypted_suvs = {}
        print("SHARED KEYS SIZE:")
        print(len(self.shared_keys))
        for key, value in self.shared_keys.items():
            value = str(value).encode('utf-8')
            key_maker = hashlib.md5(value)
            key_32 = key_maker.hexdigest().encode('utf-8')
            aes = pyaes.AESModeOfOperationCTR(key_32)

            cipher_text = []
            for item in self.suv:
                plain_text = repr(item)
                cipher_text.append(aes.encrypt(plain_text)) #encrypting suvs

            encrypted_suvs[key] = cipher_text
            print(len(self.shared_keys))
        return encrypted_suvs

    #decrypting suvs list
    def decryption(self,encrypted_suv):
        decrypted_suv = {}
        for key, value in encrypted_suv.items():
            shared_key = str(self.shared_keys[key])
            key_maker = hashlib.md5(shared_key.encode('utf-8'))
            key_32 = key_maker.hexdigest().encode('utf-8')
            aes = pyaes.AESModeOfOperationCTR(key_32)

            decrypted_suv_list=[]
            for item in value:
                decrypted = aes.decrypt(item)
                decrypted_suv_str = decrypted.decode(encoding='utf-8', errors='replace')
                decrypted_suv_list.append(eval(decrypted_suv_str))
            decrypted_suv[key] = decrypted_suv_list
        #create list of puvs : puv = suv - svu
        for key, value in decrypted_suv.items():
            puv_list = []
            for i in range(0, len(value)):
                puv_list.append(np.subtract(self.suv[i],value[i]))
            self.puvs[key] = puv_list

    def deleteVal(self):
        self.shared_keys = {}
        self.diffie_parameters = {}
        self.pub_keys = {}
        self.puvs = {}
        self.suv = []
        self.updates = []
        self.dimension = []


    def create_update(self):
        #final updates : y = model_update + sigma(puv)
        sum_puv = [] #size would depend on update dimensions
        for key, value in self.puvs.items():
            for item in value:
                sum_puv.append(np.zeros_like(item))
            break
        for key, value in self.puvs.items():
            for i in range(0, len(value)):
                sum_puv[i] = np.add(sum_puv[i], value[i]) #adding all puvs
        for i in range(0, len(self.updates)):
            self.updates[i] = np.add(self.updates[i],sum_puv[i]) #add sum_puv to updates
        updates = pd.Series(self.updates).to_json(orient='values') #convert updates to json before emitting to server
        return updates
