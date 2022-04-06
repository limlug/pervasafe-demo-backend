from fastapi import FastAPI
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import heartpy as hp

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
        heart_data = data[request_id][-3000:]
        filtered_data = hp.filter_signal(heart_data, cutoff=[0.75, 3.5], sample_rate=100.0, order=3,
                                         filtertype='bandpass')
        working_data, measures = hp.process(filtered_data, sample_rate=100.0)
        logger.debug(measures)
        return {"heartrate": float(f'{measures["bpm"]:.2f}'),
                "pnn20": float(f'{measures["pnn20"]:.2f}'),
                "breathingrate": float(f'{measures["breathingrate"]:.3f}'),
                "stressindex": 0
                }
    else:
        return {"heartrate": 0, "pnn20": 0, "breathingrate": 0, "stressindex": 0}
