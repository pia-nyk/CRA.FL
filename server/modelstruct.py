from keras.models import Sequential
from keras.layers import Dense
from keras.models import model_from_json
import numpy as np
import pandas as pd
import json

#initializing model structure and weights to send to clients
model = Sequential()
model.add(Dense(20, input_dim=43, activation="relu", kernel_initializer="uniform"))
model.add(Dense(10, activation="relu", kernel_initializer="uniform"))
model.add(Dense(1, activation="sigmoid", kernel_initializer="uniform"))
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

model_json = model.to_json()
model_weights = model.get_weights()
model_weights_json = pd.Series(model_weights).to_json(orient='values')
