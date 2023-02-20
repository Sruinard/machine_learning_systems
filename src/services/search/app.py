# create a fastapi with an endpoint to index the products and write to gcs
# and an endpoint to make lookup similar products based on a query

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import tensorflow_text
from typing import Optional, List
import os
import uvicorn
import json
import requests
import predict

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
]


LOAD_INDEX = True
SIM_MODEL = predict.create_similarity_model()
if LOAD_INDEX:
    predict.load_index(SIM_MODEL, "ml_index")



app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/index")
def index_database():
    # retrieve all products from api:
    URL = "http://localhost:8000"
    response = requests.get(
        URL + "/products")
    products = response.json()
    predict.create_index(products, SIM_MODEL, "ml_index")

@app.post("/search")
def search(query: str) -> List[str]:
    results = predict.find(query, SIM_MODEL, 5)
    return results

if __name__ == "__main__":
    port = os.getenv("PORT", 8080)
    uvicorn.run(app, host="0.0.0.0", port=port)