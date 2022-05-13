from fastapi import FastAPI
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import heartpy as hp
from sklearn import linear_model
from sklearn.linear_model import HuberRegressor
import pandas as pd
import numpy as np
import os
logger.debug(os.getcwd())
data_low_stress = pd.read_csv("./app/subject_1_low_stress.csv")
data_low_stress.columns = {"Time", "Value"}
i = 0
low_stress_windowed = []
while i < len(data_low_stress.values)-1000:
  low_stress_windowed.append(data_low_stress["Value"].values[i:i+1000])
  i += 100
low_stress_label = np.random.randint(low=0, high=30, size=np.array(low_stress_windowed).shape[0])
data_high_stress = pd.read_csv("./app/subject_1_high_stress.csv")
data_high_stress.columns = {"Time", "Value"}
i = 0
high_stress_windowed = []
while i < len(data_high_stress.values)-1000:
  high_stress_windowed.append(data_high_stress["Value"].values[i:i+1000])
  i += 100
high_stress_label = np.random.randint(low=60, high=100, size=np.array(high_stress_windowed).shape[0])
X = np.concatenate((np.array(low_stress_windowed), np.array(high_stress_windowed)), axis=0)
Y = np.concatenate((low_stress_label, high_stress_label), axis=0)
stress_index_regressor = HuberRegressor()
stress_index_regressor.fit(X, Y)
logger.debug("Startup Complete")

app = FastAPI()

origins = [
    "http://demo.pervasafe.de",
    "https://demo.pervasafe.de",
    "http://api.pervasafe.de",
    "https://api.pervasafe.de",
    "http://localhost",
    "http://localhost:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
data = {}

class DataModel(BaseModel):
    request_id: str
    data: list = []


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/data")
async def store_data(request_data: DataModel):
    if request_data.request_id not in data:
        data[request_data.request_id] = []
    for entry in request_data.data:
        data[request_data.request_id].append(entry)
    return {}


@app.get("/data/{request_id}")
async def get_data(request_id):
    if request_id in data and len(data[request_id]) > 3000:
        try:
            heart_data = data[request_id][-3000:]
            filtered_data = hp.filter_signal(heart_data, cutoff=[0.75, 3.5], sample_rate=100.0, order=3,
                                             filtertype='bandpass')
            working_data, measures = hp.process(filtered_data, sample_rate=100.0)
            stress_index = stress_index_regressor.predict([heart_data[-1000:]])
            logger.debug(measures)
            return {"heartrate": float(f'{measures["bpm"]:.2f}'),
                    "pnn20": float(f'{measures["pnn20"]:.2f}'),
                    "breathingrate": float(f'{measures["breathingrate"]:.3f}'),
                    "stressindex": int(stress_index[0]),
                    }
        except:
            return {"heartrate": 0, "pnn20": 0, "breathingrate": 0, "stressindex": 0}
    else:
        return {"heartrate": 0, "pnn20": 0, "breathingrate": 0, "stressindex": 0}
